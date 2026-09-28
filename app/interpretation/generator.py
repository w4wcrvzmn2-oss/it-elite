"""Generate interpretation JSON reports."""

from __future__ import annotations

import json
from pathlib import Path

from app.interpretation.models import (
    CheckResult,
    InterpretationReport,
    PlantingInterpretation,
    RejectedInterpretation,
)
from app.planting.models import PlantingPoint, RejectedPoint, PlantingResult
from app.rules.models import RulesCatalog


def _extract_distances(checks: list) -> dict[str, float | None]:
    """Extract measured distances from check results."""
    distances: dict[str, float | None] = {}
    for check in checks:
        if check.rule.endswith("_distance") and check.status == "passed":
            key = check.rule.replace("_distance", "")
            distances[key] = check.value
        elif check.rule == "minimum_spacing" and check.status == "passed":
            distances["nearest_planting"] = check.value
    return distances


def generate_interpretation(
    accepted: list[PlantingPoint],
    rejected: list[RejectedPoint],
    catalog: RulesCatalog,
    summary: dict | None = None,
) -> InterpretationReport:
    """Build interpretation report from planting results."""
    plantings = [
        PlantingInterpretation(
            id=p.id,
            type=p.planting_type,
            x=p.x,
            y=p.y,
            status=p.status,
            score=p.score,
            checks=[
                CheckResult(
                    rule=c.rule,
                    value=c.value,
                    required=c.required,
                    status=c.status,
                    regulation=c.regulation,
                    clause=c.clause,
                    description=c.description,
                )
                for c in p.checks
            ],
            distances=_extract_distances(p.checks),
            explanation=p.explanation,
        )
        for p in accepted
    ]

    rejected_entries = [
        RejectedInterpretation(
            x=r.x,
            y=r.y,
            type=r.planting_type,
            reason=r.reason,
            distance=r.distance,
            required=r.required,
            regulation=r.regulation,
            clause=r.clause,
        )
        for r in rejected
    ]

    type_counts: dict[str, int] = {}
    for p in accepted:
        type_counts[p.planting_type] = type_counts.get(p.planting_type, 0) + 1

    report_summary = {
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "planting_types": type_counts,
        **(summary or {}),
    }

    return InterpretationReport(
        plantings=plantings,
        rejected=rejected_entries,
        rules_applied=catalog.to_report(),
        summary=report_summary,
    )


def save_interpretation(report: InterpretationReport, output_path: Path) -> None:
    """Save interpretation report to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, ensure_ascii=False, indent=2)


def load_interpretation(filepath: Path) -> InterpretationReport:
    """Load interpretation report from JSON."""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    return InterpretationReport.model_validate(data)


def format_report_summary(report: InterpretationReport) -> str:
    """Format interpretation report as human-readable text."""
    lines = [
        "=== Planting Interpretation Report ===",
        f"Accepted plantings: {report.summary.get('accepted_count', 0)}",
        f"Rejected candidates: {report.summary.get('rejected_count', 0)}",
        "",
        "Planting types:",
    ]
    for ptype, count in report.summary.get("planting_types", {}).items():
        lines.append(f"  {ptype}: {count}")

    lines.append("")
    lines.append("Sample accepted planting:")
    if report.plantings:
        p = report.plantings[0]
        lines.extend([
            f"  ID: {p.id}",
            f"  Type: {p.type}",
            f"  Coordinates: ({p.x}, {p.y})",
            f"  Explanation: {p.explanation}",
        ])

    lines.append("")
    lines.append("Rules applied:")
    for rule in report.rules_applied[:5]:
        lines.append(
            f"  {rule['planting_type']}/{rule['restriction_type']}: "
            f"{rule['minimum_distance']}m ({rule['regulation_document']}, "
            f"{rule['regulation_clause']})"
        )

    return "\n".join(lines)
