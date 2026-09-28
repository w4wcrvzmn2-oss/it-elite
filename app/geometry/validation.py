"""Geometry validation and repair."""

from __future__ import annotations

import logging

from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.validation import make_valid

logger = logging.getLogger(__name__)


def fix_geometry(geom: BaseGeometry | None) -> BaseGeometry | None:
    """Repair invalid geometry or return None if empty."""
    if geom is None or geom.is_empty:
        return None
    if not geom.is_valid:
        fixed = make_valid(geom)
        if fixed.is_empty:
            return None
        logger.debug("Fixed invalid geometry: %s -> %s", geom.geom_type, fixed.geom_type)
        return fixed
    return geom


def to_polygons(geom: BaseGeometry | None) -> list[Polygon]:
    """Extract valid polygons from any geometry."""
    geom = fix_geometry(geom)
    if geom is None:
        return []
    if isinstance(geom, Polygon):
        return [geom] if not geom.is_empty and geom.area > 0 else []
    if isinstance(geom, MultiPolygon):
        return [p for p in geom.geoms if not p.is_empty and p.area > 0]
    return []


def safe_area(geom: BaseGeometry | None) -> float:
    """Return area of geometry, 0 if None or empty."""
    geom = fix_geometry(geom)
    if geom is None:
        return 0.0
    return float(geom.area)
