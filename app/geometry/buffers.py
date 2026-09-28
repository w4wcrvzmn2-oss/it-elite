"""Buffer and forbidden zone operations."""

from __future__ import annotations

import logging

from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from app.geometry.polygons import merge_geometries
from app.geometry.validation import fix_geometry, safe_area, to_polygons

logger = logging.getLogger(__name__)


def create_buffer(geometry: BaseGeometry, distance: float) -> BaseGeometry | None:
    """Create buffer around geometry with validation."""
    geom = fix_geometry(geometry)
    if geom is None:
        return None
    buffered = geom.buffer(distance, cap_style=2, join_style=2)
    return fix_geometry(buffered)


def create_union_buffer(
    geometries: list[BaseGeometry],
    distance: float,
) -> BaseGeometry | None:
    """Create unified buffer around multiple geometries."""
    if not geometries:
        return None

    buffered_parts = []
    for geom in geometries:
        buf = create_buffer(geom, distance)
        if buf is not None and not buf.is_empty:
            buffered_parts.append(buf)

    if not buffered_parts:
        return None

    return fix_geometry(unary_union(buffered_parts))


def create_forbidden_zone(
    restriction_geometries: dict[str, list[BaseGeometry]],
    buffer_distances: dict[str, float],
) -> tuple[BaseGeometry | None, dict[str, BaseGeometry | None]]:
    """Create combined forbidden zone from categorized restriction geometries."""
    category_buffers: dict[str, BaseGeometry | None] = {}

    for category, geoms in restriction_geometries.items():
        distance = buffer_distances.get(category, 0.0)
        if distance <= 0 or not geoms:
            category_buffers[category] = None
            continue
        category_buffers[category] = create_union_buffer(geoms, distance)

    valid_buffers = [b for b in category_buffers.values() if b is not None and not b.is_empty]
    if not valid_buffers:
        return None, category_buffers

    combined = fix_geometry(unary_union(valid_buffers))
    return combined, category_buffers


def calculate_allowed_area(
    planting_area: BaseGeometry | None,
    forbidden_zone: BaseGeometry | None,
) -> BaseGeometry | None:
    """Calculate allowed planting area by subtracting forbidden zone from planting area."""
    area = fix_geometry(planting_area)
    if area is None or area.is_empty:
        return None

    if forbidden_zone is None or forbidden_zone.is_empty:
        return area

    forbidden = fix_geometry(forbidden_zone)
    if forbidden is None or forbidden.is_empty:
        return area

    try:
        allowed = area.difference(forbidden)
    except Exception as e:
        logger.warning("Difference operation failed, retrying with buffered geometries: %s", e)
        area = area.buffer(0)
        forbidden = forbidden.buffer(0)
        allowed = area.difference(forbidden)

    allowed = fix_geometry(allowed)
    if allowed is None or allowed.is_empty:
        return None

    return allowed


def get_planting_boundary(
    boundary_geometries: list[BaseGeometry],
    fallback_geometries: list[BaseGeometry] | None = None,
) -> BaseGeometry | None:
    """Determine planting boundary from boundary layer or fallback to convex hull of all objects."""
    merged = merge_geometries(boundary_geometries)
    if merged is not None:
        polys = to_polygons(merged)
        if polys:
            return max(polys, key=lambda p: p.area)

    if fallback_geometries:
        merged_fallback = merge_geometries(fallback_geometries)
        if merged_fallback is not None:
            from shapely.geometry import MultiPoint

            coords = []
            if hasattr(merged_fallback, "geoms"):
                for g in merged_fallback.geoms:
                    if hasattr(g, "coords"):
                        coords.extend(list(g.coords))
                    elif hasattr(g, "exterior"):
                        coords.extend(list(g.exterior.coords))
            elif hasattr(merged_fallback, "exterior"):
                coords.extend(list(merged_fallback.exterior.coords))

            if coords:
                hull = MultiPoint(coords).convex_hull
                return fix_geometry(hull)

    return None
