import pytest
from fastapi.testclient import TestClient
from api.index import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "Autonomous Lead Enrichment Engine" in response.text

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_default_domains_endpoint():
    response = client.get("/api/default-domains")
    assert response.status_code == 200
    data = response.json()
    assert "domains" in data
    assert isinstance(data["domains"], list)

def test_enrich_validation_error():
    response = client.post("/enrich", json={"domains": []})
    assert response.status_code == 400

def test_favicon_endpoint():
    response = client.get("/favicon.ico")
    assert response.status_code == 204

