"""Tests for full pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.dxf.reader import read_dxf
from app.interpretation.generator import load_interpretation
from app.pipeline import PipelineError, run_pipeline
from shapely.geometry import Point


def test_full_pipeline(test_dxf_path: Path, output_dir: Path) -> None:
    output_path = output_dir / "result.dxf"
    result = run_pipeline(test_dxf_path, output_path)

    assert output_path.exists()
    assert result.interpretation_json.exists()
    assert result.run_report_json.exists()
    assert len(result.accepted_plantings) > 0


def test_interpretation(test_dxf_path: Path, output_dir: Path) -> None:
    output_path = output_dir / "result.dxf"
    run_pipeline(test_dxf_path, output_path)

    report = load_interpretation(output_dir / "interpretation.json")
    assert len(report.plantings) > 0

    for planting in report.plantings:
        assert planting.explanation
        assert planting.status == "accepted"
        assert len(planting.checks) > 0
        assert isinstance(planting.distances, dict)
        for check in planting.checks:
            assert check.regulation
            assert check.clause


def test_run_report(test_dxf_path: Path, output_dir: Path) -> None:
    output_path = output_dir / "result.dxf"
    run_pipeline(test_dxf_path, output_path)

    with open(output_dir / "run_report.json") as f:
        report = json.load(f)

    assert report["accepted_points"] > 0
    assert report["communications"] >= 1
    assert report["allowed_area"] > 0
    assert report["site_area_m2"] > 0
    assert report["density_per_1000m2"] > 0
    assert "tree" in report["planting_types"]
    assert "verification_required" in report
    assert "planting_config" in report


def test_no_planting_in_forbidden_zone(test_dxf_path: Path, output_dir: Path, config) -> None:
    output_path = output_dir / "result.dxf"
    result = run_pipeline(test_dxf_path, output_path)

    from app.geometry.buffers import create_buffer
    from app.dxf.reader import collect_geometries

    doc = read_dxf(test_dxf_path)
    pipes = collect_geometries(doc, config.layers.communications)
    buffer_dist = config.get_communication_buffer()
    forbidden_parts = [create_buffer(g, buffer_dist) for g in pipes]
    from shapely.ops import unary_union
    from app.geometry.validation import fix_geometry
    valid_parts = [p for p in forbidden_parts if p is not None]
    forbidden = fix_geometry(unary_union(valid_parts))

    for planting in result.accepted_plantings:
        pt = Point(planting.x, planting.y)
        if forbidden is not None:
            assert not forbidden.contains(pt), (
                f"Planting {planting.id} at ({planting.x}, {planting.y}) "
                f"is inside forbidden zone"
            )


def test_pipeline_no_communications(tmp_path: Path, output_dir: Path) -> None:
    """Pipeline should fail gracefully when no communication layers found."""
    import ezdxf

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (50, 0), (50, 50), (0, 50)], close=True, dxfattribs={"layer": "WALLS"})
    dxf_path = tmp_path / "no_comm.dxf"
    doc.saveas(str(dxf_path))

    with pytest.raises(PipelineError, match="No communication layers"):
        run_pipeline(dxf_path, output_dir / "result.dxf")
