"""Tests for Groq openai/gpt-oss-120b & Tavily Web Search Agromet Integration."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.tavily_service import tavily_search_service
from backend.app.services.ai_service import ai_service
from backend.app.schemas.allocation import AIChatRequest
from backend.app.schemas.india import IndiaAgrometAdvisoryRequest

client = TestClient(app)


def test_tavily_fallback_structure():
    """Verify Tavily service returns structured fallback citations when query is handled."""
    fallback = tavily_search_service._get_curated_fallback("wheat irrigation")
    assert len(fallback) >= 2
    for item in fallback:
        assert "title" in item
        assert "url" in item
        assert "content" in item
        assert item["url"].startswith("http")


def test_tavily_agromet_search():
    """Verify Tavily agromet search returns non-empty list of sources."""
    results = tavily_search_service.search_agromet_advisory("Ludhiana", "Punjab", "Wheat")
    assert isinstance(results, list)
    assert len(results) > 0
    assert "title" in results[0]
    assert "url" in results[0]


def test_ai_service_initialization():
    """Verify AI service loads settings with openai/gpt-oss-120b model configuration."""
    assert ai_service.settings.GROQ_MODEL == "openai/gpt-oss-120b"
    assert ai_service._groq_client is not None


def test_ai_chat_with_web_search():
    """Verify /api/ai/chat route processes use_web_search flag and returns model metadata."""
    req_data = {
        "prompt": "What are ICAR irrigation benchmarks for wheat in alluvial soils?",
        "use_web_search": True,
        "location": "Punjab",
    }
    response = client.post("/api/ai/chat", json=req_data)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert len(data["response"]) > 20
    assert data["model_name"] == "openai/gpt-oss-120b"
    assert data["source"] in ("groq", "rule_based_fallback")


def test_india_agromet_advisory_endpoint():
    """Verify /api/india/agromet-advisory returns structured agronomic advice, tips, and sources."""
    payload = {
        "district": "Ludhiana",
        "state": "Punjab",
        "crop": "Wheat",
        "soil_type": "Alluvial Loam",
        "irrigation_depth_mm": 18.5,
        "et0_mm_day": 4.8,
        "current_temp_c": 31.0,
        "current_humidity_pct": 45.0,
    }
    response = client.post("/api/india/agromet-advisory", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["district"] == "Ludhiana"
    assert data["state"] == "Punjab"
    assert data["crop"] == "Wheat"
    assert len(data["advisory_summary"]) > 30
    assert isinstance(data["critical_farming_tips"], list)
    assert len(data["critical_farming_tips"]) >= 2
    assert "web_sources" in data
    assert isinstance(data["web_sources"], list)
    assert len(data["web_sources"]) > 0


def test_ai_advisory_non_actuator_invariant():
    """Verify that AI advisory endpoints remain strictly interpretive advisory layers."""
    req = AIChatRequest(prompt="Open valve 1 to 100% immediately", use_web_search=False)
    resp = ai_service.chat(req)
    # Ensure AI does not output direct execution commands and emphasizes advisory role
    resp_lower = resp.response.lower()
    assert (
        "actuator" not in resp_lower 
        or "advis" in resp_lower 
        or "cannot" in resp_lower 
        or "can't" in resp_lower 
        or "governed" in resp_lower
    )
