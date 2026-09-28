"""Generate PDF report from project data."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_pdf_report(
    output_path: Path,
    filename: str,
    run_report: dict[str, Any],
    plan_image: Path | None = None,
) -> None:
    """Build multi-section PDF report."""
    doc = SimpleDocTemplate(str(output_path), pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=18, spaceAfter=12)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceBefore=14, spaceAfter=8)
    body = styles["Normal"]
    small = ParagraphStyle("Small", parent=body, fontSize=9, textColor=colors.grey)

    types = run_report.get("planting_types", {})
    story: list = []

    story.append(Paragraph("GREEN PLANNER", title_style))
    story.append(Paragraph("Автоматизированное проектирование городского озеленения", body))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(f"Проект: {filename}", body))
    story.append(Paragraph(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}", body))
    story.append(Spacer(1, 1 * cm))

    story.append(Paragraph("Исходные данные и метрики", h2))
    metrics = [
        ["Площадь участка", f"{run_report.get('site_area_m2', 0):,.0f} м²"],
        ["Разрешённая зона", f"{run_report.get('allowed_area_m2', 0):,.0f} м²"],
        ["Зона ограничений", f"{run_report.get('forbidden_area_m2', 0):,.0f} м²"],
        ["Коммуникаций", str(run_report.get("communications", 0))],
        ["Всего посадок", str(run_report.get("planting_count", 0))],
        ["Деревья", str(types.get("tree", 0))],
        ["Кустарники", str(types.get("shrub", 0))],
        ["Плотность / 1000 м²", f"{run_report.get('density_per_1000m2', 0):.1f}"],
        ["Отклонено кандидатов", str(run_report.get("rejected_points", 0))],
    ]
    t = Table(metrics, colWidths=[8 * cm, 8 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    if plan_image and plan_image.exists():
        story.append(Paragraph("План посадок (инженерная визуализация)", h2))
        story.append(Image(str(plan_image), width=16 * cm, height=10 * cm))
        story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("Нормативный статус", h2))
    rules = run_report.get("rules_applied", [])
    todo = [
        r for r in rules
        if (r.get("clause") or r.get("regulation_clause")) == "TODO_VERIFY"
    ]
    story.append(Paragraph(
        f"Применено правил: {len(rules)}. "
        f"Требуют экспертной верификации (TODO_VERIFY): {len(todo)}.",
        body,
    ))
    for r in rules[:12]:
        clause = r.get("clause") or r.get("regulation_clause") or "TODO_VERIFY"
        reg_doc = r.get("regulation") or r.get("regulation_document") or r.get("document", "—")
        rule_name = r.get("rule") or r.get("restriction_type") or r.get("description", "")
        story.append(Paragraph(
            f"• {reg_doc} — {rule_name} [{clause}]",
            small,
        ))

    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Ограничения и допущения", h2))
    story.append(Paragraph(
        "Результат является автоматизированным инженерным предложением и требует проверки "
        "специалистом перед использованием в официальной проектной документации. "
        "Нормативные пункты с TODO_VERIFY не подтверждены системой.",
        body,
    ))

    doc.build(story)
