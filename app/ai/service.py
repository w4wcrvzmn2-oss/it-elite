"""AI service layer with caching."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from app.ai.client import AIClientError, get_ai_client, get_last_ai_metrics
from app.ai.fallback import fallback_ask, fallback_explanation, fallback_report, fallback_site_summary
from app.ai.prompts import (
    PROMPT_VERSION,
    SYSTEM_ASK,
    SYSTEM_COMPARE_SCENARIOS,
    SYSTEM_EXPLAIN,
    SYSTEM_PASSPORT,
    SYSTEM_REPORT,
    SYSTEM_SITE_SUMMARY,
)
from app.ai.schemas import (
    AIAskResponse,
    AIExplanation,
    AIReport,
    AIReportSection,
    AISiteSummary,
    ScenarioComparisonAI,
    SitePassport,
)

logger = logging.getLogger(__name__)

_cache: dict[str, Any] = {}


def _cache_key(*parts: str) -> str:
    return hashlib.sha256(":".join(parts).encode()).hexdigest()


def get_ai_status() -> dict:
    client = get_ai_client()
    metrics = get_last_ai_metrics()
    base = {
        "last_latency_sec": metrics.get("latency_sec"),
        "last_tokens": metrics.get("tokens"),
        "last_error": metrics.get("last_error"),
    }
    if not client.enabled:
        return {**base, "enabled": False, "available": False, "model": client.model, "message": "ИИ отключён"}
    if not client.api_key:
        return {**base, "enabled": True, "available": False, "model": client.model, "message": "API key не настроен"}
    return {**base, "enabled": True, "available": True, "model": client.model, "message": "Подключён"}


def explain_planting(planting: dict) -> AIExplanation:
    key = _cache_key("explain", planting.get("id", ""), PROMPT_VERSION)
    if key in _cache:
        return _cache[key]

    client = get_ai_client()
    if not client.is_available:
        result = fallback_explanation(planting.get("id", ""), planting.get("explanation", ""))
        return result

    context = {
        "planting_id": planting.get("id"),
        "type": planting.get("type"),
        "x": planting.get("x"),
        "y": planting.get("y"),
        "status": planting.get("status"),
        "checks": [
            {
                "rule": c.get("rule"),
                "actual": c.get("value"),
                "required": c.get("required"),
                "status": c.get("status"),
                "regulation": c.get("regulation"),
                "clause": c.get("clause"),
            }
            for c in planting.get("checks", [])
        ],
        "distances": planting.get("distances", {}),
    }

    try:
        result = client.chat_json(SYSTEM_EXPLAIN, json.dumps(context, ensure_ascii=False), AIExplanation)
        result.ai_generated = True
        result.fallback = False
        _cache[key] = result
        return result
    except AIClientError as e:
        logger.error("AI explain failed: %s", e)
        return fallback_explanation(planting.get("id", ""), planting.get("explanation", ""))


def generate_site_summary(stats: dict, rules: list | None = None) -> AISiteSummary:
    job_id = stats.get("job_id", "unknown")
    key = _cache_key("summary", job_id, PROMPT_VERSION)
    if key in _cache:
        return _cache[key]

    client = get_ai_client()
    if not client.is_available:
        return fallback_site_summary(stats)

    context = {
        "site_area_m2": stats.get("site_area_m2"),
        "allowed_area_m2": stats.get("allowed_area_m2"),
        "forbidden_area_m2": stats.get("forbidden_area_m2"),
        "planting_count": stats.get("planting_count"),
        "tree_count": stats.get("tree_count"),
        "shrub_count": stats.get("shrub_count"),
        "communications": stats.get("communications"),
        "density_per_1000m2": stats.get("density_per_1000m2"),
        "rules_count": len(rules or []),
    }

    try:
        result = client.chat_json(
            SYSTEM_SITE_SUMMARY, json.dumps(context, ensure_ascii=False), AISiteSummary
        )
        result.ai_generated = True
        result.fallback = False
        _cache[key] = result
        return result
    except AIClientError as e:
        logger.error("AI site summary failed: %s", e)
        return fallback_site_summary(stats)


def ask_question(job_id: str, question: str, context: dict) -> AIAskResponse:
    ctx_hash = hashlib.sha256(json.dumps(context, sort_keys=True).encode()).hexdigest()[:16]
    key = _cache_key("ask", job_id, question.strip().lower(), ctx_hash, PROMPT_VERSION)
    if key in _cache:
        return _cache[key]

    client = get_ai_client()
    if not client.is_available:
        return fallback_ask(question)

    payload = {"question": question, "context": context}

    try:
        raw = client.chat_json(
            SYSTEM_ASK,
            json.dumps(payload, ensure_ascii=False),
            AIAskResponse,
        )
        raw.ai_generated = True
        raw.fallback = False
        _cache[key] = raw
        return raw
    except AIClientError as e:
        logger.error("AI ask failed: %s", e)
        return fallback_ask(question)


def generate_report(stats: dict, rules: list, plantings_sample: list) -> AIReport:
    key = _cache_key("report", stats.get("job_id", ""), PROMPT_VERSION)
    if key in _cache:
        return _cache[key]

    client = get_ai_client()
    if not client.is_available:
        return fallback_report(stats)

    context = {
        "statistics": stats,
        "rules_applied": rules[:20],
        "sample_plantings": plantings_sample[:5],
    }

    try:
        result = client.chat_json(
            SYSTEM_REPORT, json.dumps(context, ensure_ascii=False), AIReport
        )
        result.ai_generated = True
        result.fallback = False
        _cache[key] = result
        return result
    except AIClientError as e:
        logger.error("AI report failed: %s", e)
        return fallback_report(stats)


def compare_scenarios_ai(job_id: str, scenarios: list[dict]) -> ScenarioComparisonAI:
    key = _cache_key("compare", job_id, PROMPT_VERSION)
    if key in _cache:
        return _cache[key]

    client = get_ai_client()
    if not client.is_available or len(scenarios) < 2:
        return ScenarioComparisonAI(
            summary="Сравнение на основе детерминированных метрик сценариев.",
            scenario_summaries=[{"id": s["id"], "summary": s.get("description", "")} for s in scenarios],
            differences=[f"{s['name']}: {s.get('planting_count', 0)} посадок" for s in scenarios],
            ai_generated=False,
            fallback=True,
        )

    try:
        result = client.chat_json(
            SYSTEM_COMPARE_SCENARIOS,
            json.dumps({"scenarios": scenarios}, ensure_ascii=False),
            ScenarioComparisonAI,
        )
        result.ai_generated = True
        result.fallback = False
        _cache[key] = result
        return result
    except AIClientError as e:
        logger.error("AI compare failed: %s", e)
        return ScenarioComparisonAI(
            summary="ИИ временно недоступен. Используйте таблицу метрик ниже.",
            fallback=True,
            ai_generated=False,
        )


def generate_passport(stats: dict, rules: list) -> SitePassport:
    key = _cache_key("passport", stats.get("job_id", ""), PROMPT_VERSION)
    if key in _cache:
        return _cache[key]

    client = get_ai_client()
    if not client.is_available:
        return SitePassport(
            title="Паспорт участка",
            executive_summary=(
                f"Участок {stats.get('site_area_m2', 0):.0f} м², "
                f"посадок {stats.get('planting_count', 0)}."
            ),
            sections=[AIReportSection(title="Метрики", content=json.dumps(stats, ensure_ascii=False))],
            verification_notes=["Нормативные пункты TODO_VERIFY требуют экспертной проверки."],
            ai_generated=False,
            fallback=True,
        )

    context = {"statistics": stats, "rules_applied": rules[:20]}
    try:
        result = client.chat_json(SYSTEM_PASSPORT, json.dumps(context, ensure_ascii=False), SitePassport)
        result.ai_generated = True
        result.fallback = False
        _cache[key] = result
        return result
    except AIClientError as e:
        logger.error("AI passport failed: %s", e)
        return SitePassport(fallback=True, ai_generated=False)
