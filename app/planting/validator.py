"""Final validation of planting points."""

from __future__ import annotations

import logging

from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry
from shapely.prepared import prep

from app.config import AppConfig
from app.planting.models import PlantingPoint
from app.planting.optimizer import _build_explanation
from app.rules.engine import RulesEngine

logger = logging.getLogger(__name__)


class PlantingValidationError(Exception):
    """Raised when planting validation fails."""


def validate_planting(
    planting: PlantingPoint,
    allowed_area: BaseGeometry,
    rules_engine: RulesEngine,
    other_plantings: list[PlantingPoint],
    config: AppConfig,
) -> tuple[bool, list]:
    """Validate a single planting point against all hard constraints."""
    point = (planting.x, planting.y)
    pconfig = config.get_planting_config(planting.planting_type)

    prepared = prep(allowed_area)
    if not prepared.contains(Point(point)):
        return False, [{"rule": "allowed_area", "status": "failed"}]

    other_coords = [
        (p.x, p.y)
        for p in other_plantings
        if p.id != planting.id and p.planting_type == planting.planting_type
    ]

    valid, checks = rules_engine.check_point(
        point,
        planting.planting_type,
        existing_plantings=other_coords,
        min_spacing=pconfig.min_spacing,
    )
    return valid, checks


def validate_all_plantings(
    plantings: list[PlantingPoint],
    allowed_area: BaseGeometry,
    rules_engine: RulesEngine,
    config: AppConfig,
) -> list[PlantingPoint]:
    """Validate all plantings and return only valid ones."""
    valid_plantings: list[PlantingPoint] = []

    for planting in plantings:
        others = [p for p in plantings if p.id != planting.id]
        valid, checks = validate_planting(
            planting, allowed_area, rules_engine, others, config
        )
        if valid:
            planting.checks = checks
            planting.explanation = _build_explanation(planting.planting_type, checks)
            valid_plantings.append(planting)
        else:
            logger.warning(
                "Planting %s failed final validation, removing", planting.id
            )

    if len(valid_plantings) < len(plantings):
        logger.warning(
            "Removed %d invalid plantings during final validation",
            len(plantings) - len(valid_plantings),
        )

    return valid_plantings
