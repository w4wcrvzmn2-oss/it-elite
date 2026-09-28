"""Polygon utilities."""

from __future__ import annotations

from shapely.geometry import MultiPolygon, Polygon, box
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from app.geometry.validation import fix_geometry, to_polygons


def merge_geometries(geometries: list[BaseGeometry]) -> BaseGeometry | None:
    """Merge a list of geometries into a single geometry."""
    valid = [fix_geometry(g) for g in geometries]
    valid = [g for g in valid if g is not None and not g.is_empty]
    if not valid:
        return None
    if len(valid) == 1:
        return valid[0]
    return unary_union(valid)


def get_bounding_polygon(geometries: list[BaseGeometry]) -> Polygon | None:
    """Create bounding box polygon from geometries."""
    valid = [g for g in geometries if g is not None and not g.is_empty]
    if not valid:
        return None
    minx = min(g.bounds[0] for g in valid)
    miny = min(g.bounds[1] for g in valid)
    maxx = max(g.bounds[2] for g in valid)
    maxy = max(g.bounds[3] for g in valid)
    return box(minx, miny, maxx, maxy)


def largest_polygon(geom: BaseGeometry | None) -> Polygon | None:
    """Return the largest polygon from a geometry."""
    polys = to_polygons(geom)
    if not polys:
        return None
    return max(polys, key=lambda p: p.area)
