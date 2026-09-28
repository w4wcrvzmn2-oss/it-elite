"""Tests for rules engine."""

from __future__ import annotations

from shapely.geometry import LineString, box

from app.config import load_config
from app.rules.engine import RulesEngine
from app.rules.loader import load_rules_from_config


def test_rules_loading(config) -> None:
    catalog = load_rules_from_config(config)
    assert len(catalog.rules) > 0
    tree_rules = catalog.get_rules_for_type("tree")
    assert len(tree_rules) > 0


def test_rules_check_point(config) -> None:
    catalog = load_rules_from_config(config)
    pipe = LineString([(0, 50), (100, 50)])
    building = box(70, 70, 95, 95)
    road = LineString([(0, 5), (100, 5)])

    engine = RulesEngine(
        catalog,
        {
            "communication": [pipe],
            "building": [building],
            "road": [road],
        },
    )

    # Point far from all restrictions
    valid, checks = engine.check_point((20.0, 20.0), "tree")
    assert valid
    assert all(c.status in ("passed", "skipped") for c in checks)

    # Point too close to pipe
    valid_close, checks_close = engine.check_point((50.0, 51.0), "tree")
    assert not valid_close
    failed = [c for c in checks_close if c.status == "failed"]
    assert len(failed) > 0


def test_rules_report(config) -> None:
    catalog = load_rules_from_config(config)
    report = catalog.to_report()
    assert all("regulation_clause" in r for r in report)
    assert any(r["regulation_clause"] == "TODO_VERIFY" for r in report)
