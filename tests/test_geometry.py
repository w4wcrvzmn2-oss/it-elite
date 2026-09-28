"""Tests for geometry operations."""

from __future__ import annotations

from shapely.geometry import LineString, Point, box

from app.geometry.buffers import (
    calculate_allowed_area,
    create_buffer,
    create_forbidden_zone,
    create_union_buffer,
)
from app.geometry.points import (
    filter_points_in_area,
    generate_grid_points,
    min_distance_between_points,
    min_distance_to_geometries,
)
from app.geometry.validation import fix_geometry, safe_area


def test_buffer_creation() -> None:
    line = LineString([(0, 0), (10, 0)])
    buf = create_buffer(line, 2.0)
    assert buf is not None
    assert buf.area > 0


def test_union_buffer() -> None:
    lines = [LineString([(0, 0), (10, 0)]), LineString([(0, 5), (10, 5)])]
    buf = create_union_buffer(lines, 1.0)
    assert buf is not None


def test_allowed_area() -> None:
    site = box(0, 0, 100, 100)
    pipe = LineString([(10, 50), (90, 50)])
    forbidden = create_buffer(pipe, 2.0)
    allowed = calculate_allowed_area(site, forbidden)
    assert allowed is not None
    assert safe_area(allowed) < safe_area(site)


def test_point_generation() -> None:
    area = box(0, 0, 50, 50)
    points = generate_grid_points(area, step=5.0, seed=42)
    assert len(points) > 0
    filtered = filter_points_in_area(points, area)
    assert len(filtered) == len(points)


def test_minimum_spacing() -> None:
    p1 = (0.0, 0.0)
    p2 = (3.0, 4.0)
    dist = min_distance_between_points(p1, [p2])
    assert abs(dist - 5.0) < 0.01


def test_communication_distance() -> None:
    pipe = LineString([(0, 50), (100, 50)])
    point_above = (50.0, 55.0)
    point_close = (50.0, 51.0)
    geoms = [pipe]

    dist_far = min_distance_to_geometries(point_above, geoms)
    dist_close = min_distance_to_geometries(point_close, geoms)

    assert dist_far >= 4.9
    assert dist_close < 2.0


def test_forbidden_zone() -> None:
    pipe = LineString([(10, 50), (90, 50)])
    restrictions = {"communications": [pipe]}
    buffers = {"communications": 2.0}
    forbidden, cats = create_forbidden_zone(restrictions, buffers)
    assert forbidden is not None
    assert safe_area(forbidden) > 0


def test_fix_invalid_geometry() -> None:
    # Bowtie polygon (self-intersecting)
    from shapely.geometry import Polygon
    bowtie = Polygon([(0, 0), (2, 2), (2, 0), (0, 2)])
    fixed = fix_geometry(bowtie)
    assert fixed is not None
