"""Scenario service tests."""

from app.scenarios.presets import SCENARIO_PRESETS
from app.scenarios.service import compare_scenarios


def test_presets_exist():
    assert "dense" in SCENARIO_PRESETS
    assert "balanced" in SCENARIO_PRESETS
    assert "minimal" in SCENARIO_PRESETS


def test_compare_scenarios():
    scenarios = [
        {"id": "dense", "name": "Плотное", "planting_count": 100, "tree_count": 50, "shrub_count": 50},
        {"id": "minimal", "name": "Минимальное", "planting_count": 30, "tree_count": 10, "shrub_count": 20},
    ]
    result = compare_scenarios(scenarios)
    assert len(result["rows"]) > 0
    tree_row = next(r for r in result["rows"] if r["key"] == "tree_count")
    assert tree_row["values"]["dense"] == 50
