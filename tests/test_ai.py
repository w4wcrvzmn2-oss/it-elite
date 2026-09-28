"""AI layer tests (mocked — no real API calls)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.ai.fallback import fallback_explanation, fallback_site_summary
from app.ai.schemas import AIExplanation
from app.ai.service import explain_planting, get_ai_status
from app.api.main import app

client = TestClient(app)


def test_ai_status_without_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("AI_ENABLED", "true")
    from app.ai import client as ai_client_mod
    ai_client_mod._client = None

    status = get_ai_status()
    assert status["enabled"] is True
    assert status["available"] is False


def test_fallback_explanation():
    result = fallback_explanation("tree_001", "Test explanation")
    assert result.fallback is True
    assert result.ai_generated is False
    assert "Test explanation" in result.summary or result.reasons


def test_fallback_site_summary():
    stats = {"site_area_m2": 1000, "planting_count": 10, "allowed_area_m2": 800, "forbidden_area_m2": 200, "tree_count": 5, "shrub_count": 5}
    result = fallback_site_summary(stats)
    assert result.fallback is True
    assert "10" in result.summary


def test_explain_planting_no_api_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    from app.ai import client as ai_client_mod
    ai_client_mod._client = None

    planting = {
        "id": "tree_001",
        "type": "tree",
        "x": 10,
        "y": 20,
        "status": "accepted",
        "checks": [{"rule": "communication_distance", "value": 3.0, "required": 2.0, "status": "passed", "regulation": "743-ПП", "clause": "TODO_VERIFY"}],
        "explanation": "Посадка допустима.",
    }
    result = explain_planting(planting)
    assert result.fallback is True


@patch("app.ai.client.OpenRouterClient.chat_json")
def test_explain_planting_with_mock(mock_chat, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("AI_ENABLED", "true")
    from app.ai import client as ai_client_mod
    ai_client_mod._client = None
    from app.ai import service as svc
    svc._cache.clear()

    mock_chat.return_value = AIExplanation(
        title="Test",
        summary="AI summary",
        reasons=["Reason 1"],
        constraints=["Constraint 1"],
        regulatory_notes=["743-ПП"],
        verification_notes=["TODO_VERIFY requires expert"],
    )

    planting = {
        "id": "tree_001",
        "type": "tree",
        "checks": [],
        "explanation": "",
    }
    result = explain_planting(planting)
    assert result.ai_generated is True
    assert result.summary == "AI summary"


def test_ai_endpoints_exist():
    r = client.get("/api/ai/status")
    assert r.status_code == 200
    assert "enabled" in r.json()
