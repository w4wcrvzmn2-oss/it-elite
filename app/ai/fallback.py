"""Deterministic fallbacks when AI is unavailable."""

from __future__ import annotations

from app.ai.schemas import AIAskResponse, AIExplanation, AIReport, AIReportSection, AISiteSummary


def fallback_explanation(planting_id: str, explanation: str = "") -> AIExplanation:
    return AIExplanation(
        title="Почему эта посадка допустима",
        summary=explanation or "Посадка допустима по проверенным геометрическим ограничениям.",
        reasons=[explanation] if explanation else ["Все детерминированные проверки пройдены."],
        constraints=["Проверки выполнены алгоритмическим ядром Green Planner."],
        regulatory_notes=["См. interpretation.json для нормативных ссылок."],
        verification_notes=["AI недоступен — показано детерминированное объяснение."],
        ai_generated=False,
        fallback=True,
    )


def fallback_site_summary(stats: dict) -> AISiteSummary:
    return AISiteSummary(
        title="Анализ участка",
        summary=(
            f"На участке размещено {stats.get('planting_count', 0)} посадок "
            f"на {stats.get('allowed_area_m2', 0):.0f} m² допустимой площади."
        ),
        key_metrics=[
            f"Площадь участка: {stats.get('site_area_m2', 0):.0f} m²",
            f"Допустимая площадь: {stats.get('allowed_area_m2', 0):.0f} m²",
            f"Посадок: {stats.get('planting_count', 0)}",
        ],
        restrictions_overview=f"Запретная зона: {stats.get('forbidden_area_m2', 0):.0f} m²",
        planting_overview=f"Деревья: {stats.get('tree_count', 0)}, кустарники: {stats.get('shrub_count', 0)}",
        ai_generated=False,
        fallback=True,
    )


def fallback_ask(question: str) -> AIAskResponse:
    return AIAskResponse(
        answer="ИИ временно недоступен. Ниже показано объяснение на основе детерминированного расчёта.",
        ai_generated=False,
        fallback=True,
    )


def fallback_report(stats: dict) -> AIReport:
    return AIReport(
        title="Planting Analysis Report",
        overview="Отчёт сформирован на основе детерминированного анализа.",
        sections=[
            AIReportSection(title="Site metrics", content=str(stats)),
            AIReportSection(title="Note", content="AI report unavailable — deterministic data only."),
        ],
        verification_notes=["Нормативные пункты с TODO_VERIFY требуют экспертной верификации."],
        ai_generated=False,
        fallback=True,
    )
