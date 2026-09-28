"""Regression tests for DXF source integrity."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.dxf.audit import capture_source_snapshot, compare_snapshots
from app.dxf.reader import read_dxf
from app.pipeline import run_pipeline


def test_source_snapshot_regression(test_dxf_path: Path, output_dir: Path) -> None:
    """Regression: source layer names, entity counts, geometry counts unchanged."""
    output_path = output_dir / "regression_result.dxf"

    before_doc = read_dxf(test_dxf_path)
    snapshot_before = capture_source_snapshot(before_doc)

    result = run_pipeline(test_dxf_path, output_path)

    after_doc = read_dxf(output_path)
    snapshot_after = capture_source_snapshot(after_doc)

    errors = compare_snapshots(snapshot_before, snapshot_after)
    assert errors == []

    with open(result.run_report_json) as f:
        report = json.load(f)

    assert "source_snapshot_before" in report
    assert report["source_snapshot_before"]["total_entities"] == snapshot_before.total_entities
    assert report["source_snapshot_before"]["layer_names"] == snapshot_before.layer_names


def test_max_count_limit(tmp_path: Path, output_dir: Path) -> None:
    """Planting count respects max_count config."""
    import yaml

    config_path = tmp_path / "limited.yaml"
    base_config = Path(__file__).resolve().parent.parent / "config" / "default.yaml"
    with open(base_config) as f:
        cfg = yaml.safe_load(f)
    cfg["planting"]["tree"]["max_count"] = 5
    cfg["planting"]["shrub"]["enabled"] = False
    with open(config_path, "w") as f:
        yaml.dump(cfg, f)

    test_dxf = Path(__file__).resolve().parent.parent / "data" / "input" / "test.dxf"
    if not test_dxf.exists():
        pytest.skip("test.dxf not found")

    output_path = output_dir / "limited_result.dxf"
    result = run_pipeline(test_dxf, output_path, config_path)

    tree_count = sum(1 for p in result.accepted_plantings if p.planting_type == "tree")
    assert tree_count <= 5


def test_run_report_density_fields(test_dxf_path: Path, output_dir: Path) -> None:
    output_path = output_dir / "density_result.dxf"
    run_pipeline(test_dxf_path, output_path)

    with open(output_dir / "run_report.json") as f:
        report = json.load(f)

    for field in (
        "site_area_m2",
        "forbidden_area_m2",
        "allowed_area_m2",
        "planting_count",
        "density_per_1000m2",
        "planting_config",
    ):
        assert field in report, f"Missing field: {field}"

    assert "tree" in report["planting_config"]
    assert "min_spacing" in report["planting_config"]["tree"]
    assert "max_count" in report["planting_config"]["tree"]
