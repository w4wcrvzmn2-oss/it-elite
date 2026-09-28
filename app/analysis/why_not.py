"""Deterministic 'why not here' explanation for map points."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from app.interpretation.generator import load_interpretation


def _distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x2 - x1, y2 - y1)


def explain_why_not_here(
    x: float,
    y: float,
    interpretation_path: Path,
    run_report: dict,
) -> dict[str, Any]:
    report = load_interpretation(interpretation_path)
    nearest_rejected = None
    nearest_dist = float("inf")
    for r in report.rejected:
        d = _distance(x, y, r.x, r.y)
        if d < nearest_dist:
            nearest_dist = d
            nearest_rejected = r

    reasons: list[str] = []
    if nearest_rejected and nearest_dist < 15:
        reasons.append(
            f"Ближайший отклонённый кандидат ({nearest_rejected.type}) на расстоянии {nearest_dist:.1f} м: "
            f"{nearest_rejected.reason}"
        )
        if nearest_rejected.distance is not None and nearest_rejected.required is not None:
            reasons.append(
                f"Измеренное расстояние {nearest_rejected.distance:.1f} м, требуется ≥ {nearest_rejected.required:.1f} м."
            )
    else:
        reasons.append("В этой точке нет принятой посадки — алгоритм не разместил здесь растение.")
        reasons.append(
            "Возможные причины: конфликт с ограничениями, недостаточное расстояние до объектов "
            "или оптимизатор выбрал другие точки с лучшим счётом."
        )

    return {
        "title": "Почему здесь нет посадки?",
        "x": x,
        "y": y,
        "reasons": reasons,
        "nearest_rejection": (
            {
                "type": nearest_rejected.type,
                "reason": nearest_rejected.reason,
                "distance_m": nearest_rejected.distance,
                "required_m": nearest_rejected.required,
                "regulation": nearest_rejected.regulation,
                "clause": nearest_rejected.clause,
            }
            if nearest_rejected and nearest_dist < 15
            else None
        ),
        "site_context": {
            "allowed_area_m2": run_report.get("allowed_area_m2"),
            "forbidden_area_m2": run_report.get("forbidden_area_m2"),
            "rejected_total": run_report.get("rejected_points", 0),
        },
        "verification_notes": [
            "Объяснение основано на детерминированных результатах расчёта.",
        ],
    }


def build_why_here_deterministic(planting: dict) -> dict[str, Any]:
    checks = planting.get("checks", [])
    distances = planting.get("distances", {})
    reasons = [
        "Точка находится внутри разрешённой зоны.",
        "Минимальные расстояния до ограничивающих объектов соблюдены.",
    ]
    for key, label in [
        ("communication", "коммуникации"),
        ("building", "здания"),
        ("road", "дороги"),
    ]:
        val = distances.get(key)
        if val is not None:
            reasons.append(f"До ближайшей {label}: {val:.1f} м.")

    spacing = distances.get("nearest_planting")
    if spacing is not None:
        reasons.append(f"До соседней посадки: {spacing:.1f} м.")

    reasons.append("Все проверенные геометрические ограничения соблюдены.")

    todo = [c for c in checks if c.get("clause") == "TODO_VERIFY"]
    verification = []
    if todo:
        verification.append(
            "Применённое правило требует экспертной проверки перед использованием в официальном проекте."
        )

    return {
        "title": f"Почему здесь можно посадить {'дерево' if planting.get('type') == 'tree' else 'кустарник'}?",
        "reasons": reasons,
        "checks_passed": len([c for c in checks if c.get("status") == "passed"]),
        "verification_notes": verification,
        "geometry_valid": True,
    }
