import json
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from backend.main import app
from src.schemas import CompanyIntelligence

client = TestClient(app)

def test_api_health_endpoint():
    """Verify health endpoint returns ok and environment flags without leaking secrets."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert "environment" in data
    assert "GROQ_API_KEY_configured" in data["environment"]
    assert "SERPAPI_API_KEY_configured" in data["environment"]


def test_api_openapi_and_docs():
    """Verify openapi schema and documentation endpoints exist under /api."""
    res_open = client.get("/api/openapi.json")
    assert res_open.status_code == 200
    paths = res_open.json()["paths"]
    assert "/api/health" in paths
    assert "/api/enrich/stream" in paths


def test_validation_empty_domains():
    """Verify rejection of empty domain list."""
    response = client.post("/api/enrich/stream", json={"domains": []})
    assert response.status_code == 400
    assert "Domain list cannot be empty" in response.json()["detail"]


def test_validation_invalid_domain():
    """Verify rejection of malformed domain string."""
    response = client.post("/api/enrich/stream", json={"domains": ["not_a_valid_domain"]})
    assert response.status_code == 400
    assert "Invalid domain format" in response.json()["detail"]


def test_validation_ssrf_and_private_ip():
    """Verify rejection of localhost and private IP addresses."""
    # Localhost
    r_local = client.post("/api/enrich/stream", json={"domains": ["localhost"]})
    assert r_local.status_code == 400
    assert "not permitted" in r_local.json()["detail"]

    # Private IP
    r_priv = client.post("/api/enrich/stream", json={"domains": ["192.168.1.1"]})
    assert r_priv.status_code == 400
    assert "reserved/private range" in r_priv.json()["detail"]


def test_validation_duplicate_domains_deduplication():
    """Verify duplicate domains are deduplicated cleanly."""
    mock_intel = CompanyIntelligence(
        domain="stripe.com",
        company_name="Stripe",
        company_overview="Financial infrastructure",
        confidence_score=0.9,
        llm_confidence_score=0.9,
        heuristic_confidence_score=0.9,
        extraction_status="Complete"
    )

    with patch("backend.main.process_domain", new=AsyncMock(return_value=mock_intel)):
        with patch("src.browser.BrowserManager.start", new=AsyncMock()):
            with patch("src.browser.BrowserManager.stop", new=AsyncMock()):
                response = client.post(
                    "/api/enrich/stream",
                    json={"domains": ["stripe.com", "STRIPE.COM", "https://stripe.com/"]}
                )
                assert response.status_code == 200
                lines = [l for l in response.iter_lines() if l]
                # After deduplication, started event should have total: 1
                started_line = next(l for l in lines if "started" in l)
                assert started_line == "event: started"
                data_line = lines[lines.index(started_line) + 1]
                data = json.loads(data_line.replace("data: ", ""))
                assert data["total"] == 1


def test_validation_exceeding_domain_count():
    """Verify rejection when domain count exceeds allowed maximum."""
    domains = [f"domain{i}.com" for i in range(10)]
    response = client.post("/api/enrich/stream", json={"domains": domains})
    assert response.status_code == 400
    assert "Maximum" in response.json()["detail"]


def test_streaming_success_and_failure_isolation():
    """Verify SSE streaming with one successful domain and one failed domain."""
    def fake_process(domain, bm):
        if domain == "error.com":
            raise RuntimeError("Scraper network timeout")
        return CompanyIntelligence(
            domain=domain,
            company_name="SuccessCorp",
            company_overview="Cloud analytics",
            confidence_score=0.88,
            llm_confidence_score=0.9,
            heuristic_confidence_score=0.86,
            extraction_status="Complete"
        )

    with patch("backend.main.process_domain", new=AsyncMock(side_effect=fake_process)):
        with patch("src.browser.BrowserManager.start", new=AsyncMock()) as mock_start:
            with patch("src.browser.BrowserManager.stop", new=AsyncMock()) as mock_stop:
                response = client.post(
                    "/api/enrich/stream",
                    json={"domains": ["valid.com", "error.com"]}
                )
                assert response.status_code == 200
                assert mock_start.called
                assert mock_stop.called

                events = []
                current_event = None
                for line in response.iter_lines():
                    if not line:
                        continue
                    if line.startswith("event: "):
                        current_event = line.replace("event: ", "").strip()
                    elif line.startswith("data: "):
                        data = json.loads(line.replace("data: ", "").strip())
                        events.append((current_event, data))

                event_types = [e[0] for e in events]
                assert "started" in event_types
                assert "domain_started" in event_types
                assert "domain_completed" in event_types
                assert "domain_failed" in event_types
                assert "completed" in event_types

                completed_event = next(e for e in events if e[0] == "completed")[1]
                assert completed_event["success_count"] == 1
                assert completed_event["failure_count"] == 1
                assert completed_event["total"] == 2


def test_missing_api_credentials_in_health(monkeypatch):
    """Verify health endpoint accurately reports when credentials are unset."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)

    response = client.get("/api/health")
    assert response.status_code == 200
    env = response.json()["environment"]
    assert env["GROQ_API_KEY_configured"] is False
    assert env["SERPAPI_API_KEY_configured"] is False


def test_batch_timeout_budget_handling(monkeypatch):
    """Verify that exceeding BATCH_TIMEOUT_SECONDS triggers timeout fallback gracefully."""
    # Set timeout budget to 0 to trigger immediate timeout
    monkeypatch.setattr("backend.main.BATCH_TIMEOUT_SECONDS", 0)

    with patch("src.browser.BrowserManager.start", new=AsyncMock()):
        with patch("src.browser.BrowserManager.stop", new=AsyncMock()):
            response = client.post(
                "/api/enrich/stream",
                json={"domains": ["timeoutcorp.com"]}
            )
            assert response.status_code == 200
            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    events.append(json.loads(line.replace("data: ", "")))

            failed_event = next((e for e in events if e.get("status") == "failed"), None)
            assert failed_event is not None
            assert "timeout" in failed_event["error"].lower()
            assert failed_event["result"]["confidence_score"] == 0.0


def test_client_disconnect_stops_pipeline():
    """Verify that client disconnection breaks the streaming loop cleanly."""
    with patch("fastapi.Request.is_disconnected", new=AsyncMock(return_value=True)):
        with patch("src.browser.BrowserManager.start", new=AsyncMock()) as mock_start:
            with patch("src.browser.BrowserManager.stop", new=AsyncMock()) as mock_stop:
                response = client.post(
                    "/api/enrich/stream",
                    json={"domains": ["disconnect.com"]}
                )
                assert response.status_code == 200
                assert mock_start.called
                assert mock_stop.called

