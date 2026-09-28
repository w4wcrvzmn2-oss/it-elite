"""Generate export artifacts: CSV, constraints.json, summary.md, ZIP."""

from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from app.interpretation.generator import load_interpretation


def _rule_label(rule: str) -> str:
    return {
        "communication_distance": "communication",
        "building_distance": "building",
        "road_distance": "road",
        "minimum_spacing": "nearest_plant",
    }.get(rule, rule)


def generate_planting_csv(interpretation_path: Path) -> str:
    report = load_interpretation(interpretation_path)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "id", "type", "x", "y", "status",
        "distance_to_communication", "distance_to_building", "distance_to_road",
        "distance_to_restricted", "nearest_plant", "validation_status", "normative_status",
    ])
    for p in report.plantings:
        dist = p.distances
        has_todo = any(c.clause == "TODO_VERIFY" for c in p.checks)
        writer.writerow([
            p.id,
            p.type,
            round(p.x, 2),
            round(p.y, 2),
            p.status,
            dist.get("communication"),
            dist.get("building"),
            dist.get("road"),
            dist.get("restricted"),
            dist.get("nearest_planting"),
            "passed" if p.status == "accepted" else p.status,
            "needs_verification" if has_todo else "checked",
        ])
    return buf.getvalue()


def generate_constraints_json(run_report: dict, interpretation_path: Path | None = None) -> dict:
    rules = run_report.get("rules_applied", [])
    todo_rules = [
        r for r in rules
        if (r.get("clause") or r.get("regulation_clause")) == "TODO_VERIFY"
    ]
    report = load_interpretation(interpretation_path) if interpretation_path and interpretation_path.exists() else None
    return {
        "site": {
            "area_m2": run_report.get("site_area_m2"),
            "allowed_area_m2": run_report.get("allowed_area_m2"),
            "forbidden_area_m2": run_report.get("forbidden_area_m2"),
        },
        "objects": {
            "communications": run_report.get("communications", 0),
        },
        "restricted_zones": {"area_m2": run_report.get("forbidden_area_m2")},
        "allowed_zones": {"area_m2": run_report.get("allowed_area_m2")},
        "rules": rules,
        "verification_status": {
            "todo_verify_count": len(todo_rules),
            "requires_expert_verification": len(todo_rules) > 0,
        },
        "statistics": {
            "planting_count": run_report.get("planting_count"),
            "tree_count": run_report.get("planting_types", {}).get("tree", 0),
            "shrub_count": run_report.get("planting_types", {}).get("shrub", 0),
            "rejected_points": run_report.get("rejected_points", 0),
        },
        "rejected_sample_count": len(report.rejected) if report else 0,
    }


def generate_project_summary_md(filename: str, run_report: dict) -> str:
    types = run_report.get("planting_types", {})
    lines = [
        "# Green Planner — краткое описание проекта",
        "",
        f"**Исходный DXF:** {filename}",
        f"**Дата:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Площадь участка",
        f"- Площадь участка: {run_report.get('site_area_m2', 0):,.0f} м²",
        f"- Разрешённая зона: {run_report.get('allowed_area_m2', 0):,.0f} м²",
        f"- Зона ограничений: {run_report.get('forbidden_area_m2', 0):,.0f} м²",
        "",
        "## Озеленение",
        f"- Всего посадок: {run_report.get('planting_count', 0):,}",
        f"- Деревья: {types.get('tree', 0):,}",
        f"- Кустарники: {types.get('shrub', 0):,}",
        f"- Плотность: {run_report.get('density_per_1000m2', 0):.1f} / 1000 м²",
        "",
        "## Ограничения",
        f"- Коммуникаций: {run_report.get('communications', 0)}",
        f"- Отклонённых кандидатов: {run_report.get('rejected_points', 0):,}",
        "",
        "## Метод",
        "Автоматический расчёт на основе детерминированного ядра Green Planner.",
        "",
        "## Нормативная проверка",
        "⚠ Нормативные пункты с TODO_VERIFY требуют экспертной верификации.",
        "",
        "## Ограничение ответственности",
        "Результат является автоматизированным инженерным предложением "
        "и требует проверки специалистом перед использованием в официальной проектной документации.",
    ]
    return "\n".join(lines)


def generate_readme_txt() -> str:
    return """Green Planner — комплект файлов проекта

01_result/result.dxf — результат озеленения (исходные слои сохранены)
02_analysis/ — JSON отчёты и ограничения
03_planting/planting.csv — таблица посадок
04_scenarios/ — варианты сценариев (если рассчитаны)
05_report/ — текстовый отчёт
06_visualizations/ — визуализации (если созданы)

Откройте result.dxf в CAD-системе.
interpretation.json содержит проверки каждой посадки.
Нормативные пункты TODO_VERIFY требуют экспертной проверки.
"""


def write_job_exports(output_dir: Path, filename: str, run_report: dict) -> None:
    interp_path = output_dir / "interpretation.json"
    (output_dir / "planting.csv").write_text(
        generate_planting_csv(interp_path), encoding="utf-8"
    )
    (output_dir / "constraints.json").write_text(
        json.dumps(generate_constraints_json(run_report, interp_path), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "project_summary.md").write_text(
        generate_project_summary_md(filename, run_report), encoding="utf-8"
    )
    _write_pdf_if_possible(output_dir, filename, run_report)


def _write_pdf_if_possible(output_dir: Path, filename: str, run_report: dict) -> None:
    try:
        from app.export.pdf_report import generate_pdf_report

        plan = output_dir / "visualizations" / "plan_overview.png"
        if not plan.exists():
            plan = output_dir / "visualizations" / "overview.png"
        generate_pdf_report(
            output_dir / "project_report.pdf",
            filename,
            run_report,
            plan if plan.exists() else None,
        )
    except Exception:
        pass


def build_export_package(output_dir: Path, filename: str, run_report: dict) -> bytes:
    write_job_exports(output_dir, filename, run_report)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        mapping = [
            ("01_result/result.dxf", output_dir / "result.dxf"),
            ("02_analysis/run_report.json", output_dir / "run_report.json"),
            ("02_analysis/constraints.json", output_dir / "constraints.json"),
            ("02_analysis/interpretation.json", output_dir / "interpretation.json"),
            ("03_planting/planting.csv", output_dir / "planting.csv"),
            ("05_report/project_summary.md", output_dir / "project_summary.md"),
            ("05_report/project_report.pdf", output_dir / "project_report.pdf"),
        ]
        for arc, path in mapping:
            if path.exists():
                zf.write(path, arc)
        scenarios_dir = output_dir / "scenarios"
        if scenarios_dir.exists():
            for scenario in scenarios_dir.iterdir():
                if scenario.is_dir():
                    for f in scenario.iterdir():
                        if f.is_file():
                            zf.write(f, f"04_scenarios/{scenario.name}/{f.name}")
        viz_dir = output_dir / "visualizations"
        if viz_dir.exists():
            for f in viz_dir.glob("*.png"):
                zf.write(f, f"06_visualizations/{f.name}")
            for f in viz_dir.glob("*.jpg"):
                zf.write(f, f"06_visualizations/{f.name}")
        zf.writestr("README.txt", generate_readme_txt())
    return buf.getvalue()
