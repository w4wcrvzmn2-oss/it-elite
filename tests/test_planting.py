"""Tests for planting generation."""

from __future__ import annotations

from shapely.geometry import LineString, box

from app.geometry.buffers import calculate_allowed_area, create_buffer
from app.planting.generator import generate_candidates
from app.planting.optimizer import optimize_placements
from app.rules.engine import RulesEngine
from app.rules.loader import load_rules_from_config


def test_point_generation(config) -> None:
    area = box(0, 0, 100, 100)
    pipe = LineString([(10, 50), (90, 50)])
    forbidden = create_buffer(pipe, 2.0)
    allowed = calculate_allowed_area(area, forbidden)

    candidates = generate_candidates(allowed, "tree", config)
    assert len(candidates) > 0


def test_optimization(config) -> None:
    area = box(0, 0, 100, 100)
    pipe = LineString([(10, 50), (90, 50)])
    forbidden = create_buffer(pipe, 2.0)
    allowed = calculate_allowed_area(area, forbidden)

    catalog = load_rules_from_config(config)
    restrictions = {"communication": [pipe], "building": [], "road": []}
    engine = RulesEngine(catalog, restrictions)

    candidates = generate_candidates(allowed, "tree", config)
    accepted, rejected = optimize_placements(
        candidates, "tree", config, engine, restrictions, allowed
    )

    assert len(accepted) > 0
    assert len(accepted) + len(rejected) == len(candidates)

    # No accepted point should be inside pipe buffer
    for p in accepted:
        dist = min(
            ((p.x - x) ** 2 + (p.y - y) ** 2) ** 0.5
            for x, y in [(10, 50), (50, 50), (90, 50)]
        )
        # Check distance to pipe line
        from shapely.geometry import Point
        pipe_dist = Point(p.x, p.y).distance(pipe)
        assert pipe_dist >= config.get_type_rules("tree").communication.minimum_distance


def test_minimum_spacing(config) -> None:
    area = box(0, 0, 100, 100)
    catalog = load_rules_from_config(config)
    restrictions = {"communication": [], "building": [], "road": []}
    engine = RulesEngine(catalog, restrictions)

    candidates = generate_candidates(area, "tree", config)
    accepted, _ = optimize_placements(
        candidates, "tree", config, engine, restrictions, area
    )

    min_spacing = config.get_planting_config("tree").min_spacing
    for i, p1 in enumerate(accepted):
        for p2 in accepted[i + 1:]:
            dist = ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5
            assert dist >= min_spacing - 0.01
