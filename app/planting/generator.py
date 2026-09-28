"""Candidate point generation."""

from __future__ import annotations

import logging

from shapely.geometry.base import BaseGeometry

from app.config import AppConfig
from app.geometry.points import generate_grid_points
from app.planting.models import RejectedPoint

logger = logging.getLogger(__name__)


def generate_candidates(
    allowed_area: BaseGeometry,
    planting_type: str,
    config: AppConfig,
) -> list[tuple[float, float]]:
    """Generate candidate planting points for a given type."""
    pconfig = config.get_planting_config(planting_type)
    if not pconfig.enabled:
        return []

    step = pconfig.candidate_grid_step
    seed = config.project.random_seed

    points = generate_grid_points(allowed_area, step, seed=seed)
    logger.info(
        "Generated %d candidate points for %s (step=%.1f)",
        len(points),
        planting_type,
        step,
    )
    return points
