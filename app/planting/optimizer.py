"""Greedy planting optimization."""

from __future__ import annotations

import logging

from shapely.geometry.base import BaseGeometry

from app.config import AppConfig
from app.geometry.points import min_distance_to_geometries
from app.planting.models import PlantingPoint, RejectedPoint
from app.rules.engine import RulesEngine
from app.rules.models import AppliedRule

logger = logging.getLogger(__name__)


def score_point(
    point: tuple[float, float],
    restriction_geometries: dict[str, list[BaseGeometry]],
    allowed_area: BaseGeometry,
) -> float:
    """Score a candidate point (higher is better). Does not override hard constraints."""
    score = 0.0

    for category, geoms in restriction_geometries.items():
        if geoms:
            dist = min_distance_to_geometries(point, geoms)
            weight = {"communication": 2.0, "building": 1.5, "road": 1.0}.get(category, 1.0)
            score += min(dist, 20.0) * weight

    from shapely.geometry import Point

    pt = Point(point)
    centroid = allowed_area.centroid
    dist_to_center = pt.distance(centroid)
    score += max(0, 50.0 - dist_to_center) * 0.1

    return score


def _effective_max_count(
    pconfig,
    allowed_area: BaseGeometry,
) -> int | None:
    """Compute effective planting cap from max_count and/or target_density."""
    limits: list[int] = []
    if pconfig.max_count is not None:
        limits.append(pconfig.max_count)
    if pconfig.target_density is not None and allowed_area is not None:
        area_m2 = allowed_area.area
        density_limit = int(area_m2 / 1000.0 * pconfig.target_density)
        limits.append(max(0, density_limit))
    if not limits:
        return None
    return min(limits)


def optimize_placements(
    candidates: list[tuple[float, float]],
    planting_type: str,
    config: AppConfig,
    rules_engine: RulesEngine,
    restriction_geometries: dict[str, list[BaseGeometry]],
    allowed_area: BaseGeometry,
    start_index: int = 0,
) -> tuple[list[PlantingPoint], list[RejectedPoint]]:
    """Greedy selection of planting points from candidates."""
    pconfig = config.get_planting_config(planting_type)
    min_spacing = pconfig.min_spacing
    max_count = _effective_max_count(pconfig, allowed_area)

    scored = [
        (pt, score_point(pt, restriction_geometries, allowed_area))
        for pt in candidates
    ]
    scored.sort(key=lambda x: -x[1])

    accepted: list[PlantingPoint] = []
    rejected: list[RejectedPoint] = []
    accepted_coords: list[tuple[float, float]] = []

    for i, (point, point_score) in enumerate(scored):
        if max_count is not None and len(accepted) >= max_count:
            rejected.append(
                RejectedPoint(
                    x=point[0],
                    y=point[1],
                    planting_type=planting_type,
                    reason="max_count_reached",
                    distance=None,
                    required=float(max_count),
                    regulation="CONFIG",
                    clause="planting.max_count",
                )
            )
            continue

        valid, checks = rules_engine.check_point(
            point,
            planting_type,
            existing_plantings=accepted_coords,
            min_spacing=min_spacing,
        )

        if not valid:
            failed = next((c for c in checks if c.status == "failed"), None)
            rejected.append(
                RejectedPoint(
                    x=point[0],
                    y=point[1],
                    planting_type=planting_type,
                    reason=failed.rule if failed else "unknown",
                    distance=failed.value if failed else None,
                    required=failed.required if failed else None,
                    regulation=failed.regulation if failed else "",
                    clause=failed.clause if failed else "TODO_VERIFY",
                )
            )
            continue

        planting_id = f"{planting_type}_{start_index + len(accepted) + 1:03d}"
        explanation = _build_explanation(planting_type, checks)

        accepted.append(
            PlantingPoint(
                id=planting_id,
                planting_type=planting_type,
                x=round(point[0], 2),
                y=round(point[1], 2),
                status="accepted",
                score=round(point_score, 2),
                checks=checks,
                explanation=explanation,
            )
        )
        accepted_coords.append((round(point[0], 2), round(point[1], 2)))

    logger.info(
        "Optimized %s: %d accepted, %d rejected from %d candidates",
        planting_type,
        len(accepted),
        len(rejected),
        len(candidates),
    )
    return accepted, rejected


def _build_explanation(planting_type: str, checks: list[AppliedRule]) -> str:
    passed_checks = [c for c in checks if c.status == "passed"]
    if not passed_checks:
        return f"Посадка типа {planting_type} принята."

    parts = []
    for check in passed_checks:
        if check.rule == "minimum_spacing":
            parts.append(
                f"расстояние до ближайшей посадки {check.value} м "
                f"(требуется ≥ {check.required} м)"
            )
        elif check.value is not None:
            parts.append(
                f"расстояние до {check.rule.replace('_distance', '')} "
                f"составляет {check.value} м при требовании ≥ {check.required} м "
                f"({check.regulation}, {check.clause})"
            )

    return f"Посадка типа {planting_type} допустима: " + "; ".join(parts) + "."
