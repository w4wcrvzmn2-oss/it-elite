"""Point generation utilities."""

from __future__ import annotations

import numpy as np
from shapely.geometry import Point, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.prepared import prep
from shapely.strtree import STRtree

from app.geometry.validation import to_polygons


def generate_grid_points(
    area: BaseGeometry,
    step: float,
    seed: int = 42,
) -> list[tuple[float, float]]:
    """Generate a regular grid of candidate points within area bounding box."""
    if area is None or area.is_empty:
        return []

    minx, miny, maxx, maxy = area.bounds
    xs = np.arange(minx + step / 2, maxx, step)
    ys = np.arange(miny + step / 2, maxy, step)

    prepared = prep(area)
    points: list[tuple[float, float]] = []

    rng = np.random.default_rng(seed)
    offset_x = float(rng.uniform(0, step * 0.1))
    offset_y = float(rng.uniform(0, step * 0.1))

    for x in xs:
        for y in ys:
            px, py = float(x + offset_x), float(y + offset_y)
            if prepared.contains(Point(px, py)):
                points.append((px, py))

    return points


def filter_points_in_area(
    points: list[tuple[float, float]],
    area: BaseGeometry,
) -> list[tuple[float, float]]:
    """Filter points to those inside area."""
    if area is None or area.is_empty:
        return []
    prepared = prep(area)
    return [(x, y) for x, y in points if prepared.contains(Point(x, y))]


def min_distance_to_geometries(
    point: tuple[float, float],
    geometries: list[BaseGeometry],
    tree: STRtree | None = None,
) -> float:
    """Calculate minimum distance from point to any geometry."""
    if not geometries:
        return float("inf")

    pt = Point(point)
    if tree is not None:
        nearest_idx = tree.nearest(pt)
        if nearest_idx is not None:
            if isinstance(nearest_idx, (list, np.ndarray)):
                indices = nearest_idx
            else:
                indices = [nearest_idx]
            min_dist = float("inf")
            for idx in indices:
                dist = pt.distance(geometries[int(idx)])
                min_dist = min(min_dist, dist)
            return min_dist

    return min(pt.distance(g) for g in geometries)


def min_distance_between_points(
    point: tuple[float, float],
    others: list[tuple[float, float]],
) -> float:
    """Minimum distance from point to a list of other points."""
    if not others:
        return float("inf")
    arr = np.asarray(others, dtype=np.float64)
    if arr.size == 0:
        return float("inf")
    delta = arr - np.asarray(point, dtype=np.float64)
    return float(np.hypot(delta[:, 0], delta[:, 1]).min())


def build_strtree(geometries: list[BaseGeometry]) -> STRtree | None:
    """Build spatial index for geometries."""
    valid = [g for g in geometries if g is not None and not g.is_empty]
    if not valid:
        return None
    return STRtree(valid)


def split_area_polygons(area: BaseGeometry) -> list[Polygon]:
    """Split area into individual polygons."""
    return to_polygons(area)
