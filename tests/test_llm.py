import pytest
from src.llm import repair_llm_json, calculate_heuristic_confidence, get_extraction_tool_schema
from src.schemas import CompanyIntelligence

def test_get_extraction_tool_schema():
    schema = get_extraction_tool_schema()
    assert schema["type"] == "object"
    props = schema["properties"]
    assert "company_name" in props
    assert "company_overview" in props
    assert "llm_confidence_score" in props
    assert "confidence_rationale" in props
    # Excluded fields should not be in tool schema
    assert "domain" not in props
    assert "total_tokens_used" not in props
    assert "estimated_cost_usd" not in props

def test_repair_llm_json_fallback():
    raw_data = {
        "Company Name": "Test Corp",
        "Company Overview": {"text": "We build software."},
        "Products": ["Product A"],
        "llm_confidence_score": "0.85",
        "confidence_rationale": "High confidence."
    }
    repaired = repair_llm_json(raw_data, "testcorp.com", ["https://testcorp.com"])
    assert repaired["company_name"] == "Test Corp"
    assert repaired["company_overview"] == "We build software."
    assert repaired["llm_confidence_score"] == 0.85
    assert repaired["confidence_rationale"] == "High confidence."

def test_calculate_heuristic_confidence():
    intel_dict = {
        "company_overview": "Overview sentence one. Overview sentence two.",
        "products_services": [{"name": "Product 1", "description": "Desc", "source_url": "https://example.com"}],
        "leadership": [],
        "contact_points": []
    }
    # 1.0 - 0.3 (leadership) - 0.1 (contact) = 0.6
    score = calculate_heuristic_confidence(intel_dict)
    assert score == 0.6

def test_calculate_heuristic_confidence_fill_rate_ordering():
    incomplete_leadership = {
        "company_overview": "Overview sentence one. Overview sentence two.",
        "products_services": [{"name": "Product 1", "description": "Desc 1", "source_url": "https://example.com/p1"}],
        "leadership": [{"name": "John Doe", "role": "", "linkedin_url": None, "source_url": ""}],
        "contact_points": [{"value": "info@example.com", "source_url": "https://example.com"}]
    }

    fully_populated_leadership = {
        "company_overview": "Overview sentence one. Overview sentence two.",
        "products_services": [{"name": "Product 1", "description": "Desc 1", "source_url": "https://example.com/p1"}],
        "leadership": [{"name": "John Doe", "role": "CEO", "linkedin_url": "https://linkedin.com/in/johndoe", "source_url": "https://example.com/about"}],
        "contact_points": [{"value": "info@example.com", "source_url": "https://example.com"}]
    }

    score_incomplete = calculate_heuristic_confidence(incomplete_leadership)
    score_full = calculate_heuristic_confidence(fully_populated_leadership)

    assert score_incomplete < score_full

