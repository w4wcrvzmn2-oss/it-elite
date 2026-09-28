"""End-to-end tests on complex synthetic DXF."""

from __future__ import annotations

import json
from pathlib import Path

import ezdxf
import pytest
from shapely.geometry import Point

from app.dxf.audit import capture_source_snapshot, compare_snapshots
from app.dxf.reader import inspect_dxf, read_dxf
from app.geometry.buffers import create_buffer, create_forbidden_zone, calculate_allowed_area
from app.geometry.validation import safe_area
from app.pipeline import run_pipeline


@pytest.fixture
def complex_dxf_path(tmp_path: Path) -> Path:
    """Complex DXF with multiple communications, buildings, roads."""
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 6
    for layer in ("SITE", "PIPE", "WATER", "GAS", "BUILDINGS", "ROADS"):
        doc.layers.add(layer)
    msp = doc.modelspace()

    msp.add_lwpolyline(
        [(0, 0), (200, 0), (200, 150), (0, 150)],
        close=True,
        dxfattribs={"layer": "SITE"},
    )
    msp.add_lwpolyline(
        [(80, 60), (120, 60), (120, 90), (80, 90)],
        close=True,
        dxfattribs={"layer": "BUILDINGS"},
    )
    msp.add_lwpolyline(
        [(160, 110), (195, 110), (195, 145), (160, 145)],
        close=True,
        dxfattribs={"layer": "BUILDINGS"},
    )
    msp.add_line((20, 75), (180, 75), dxfattribs={"layer": "PIPE"})
    msp.add_line((100, 10), (100, 140), dxfattribs={"layer": "WATER"})
    msp.add_line((40, 30), (160, 120), dxfattribs={"layer": "GAS"})
    msp.add_line((0, 8), (200, 8), dxfattribs={"layer": "ROADS"})
    msp.add_line((0, 142), (200, 142), dxfattribs={"layer": "ROADS"})

    path = tmp_path / "synthetic_complex.dxf"
    doc.saveas(str(path))
    return path


def test_complex_dxf_inspect(complex_dxf_path: Path) -> None:
    info = inspect_dxf(complex_dxf_path)
    assert info["total_entities"] >= 8
    assert "PIPE" in info["layers"]
    assert "WATER" in info["layers"]
    assert "GAS" in info["layers"]
    assert info["units"]["insunits"] == 6
    assert info["units"]["units_name"] == "meters"


def test_complex_e2e_pipeline(complex_dxf_path: Path, output_dir: Path) -> None:
    output_path = output_dir / "complex_result.dxf"
    result = run_pipeline(complex_dxf_path, output_path)

    assert output_path.exists()
    assert result.interpretation_json.exists()
    assert result.run_report_json.exists()
    assert len(result.accepted_plantings) > 0

    with open(result.run_report_json) as f:
        report = json.load(f)

    assert report["site_area_m2"] > 0
    assert report["forbidden_area_m2"] > 0
    assert report["allowed_area_m2"] > 0
    assert report["planting_count"] > 0
    assert report["density_per_1000m2"] > 0
    assert report["communications"] >= 3
    assert "planting_config" in report


def test_complex_source_layers_preserved(complex_dxf_path: Path, output_dir: Path) -> None:
    output_path = output_dir / "complex_result.dxf"

    before_doc = read_dxf(complex_dxf_path)
    snapshot_before = capture_source_snapshot(before_doc)

    run_pipeline(complex_dxf_path, output_path)

    after_doc = read_dxf(output_path)
    snapshot_after = capture_source_snapshot(after_doc)

    errors = compare_snapshots(snapshot_before, snapshot_after)
    assert errors == [], f"Source layers modified: {errors}"


def test_complex_no_planting_in_forbidden(complex_dxf_path: Path, output_dir: Path, config) -> None:
    output_path = output_dir / "complex_result.dxf"
    result = run_pipeline(complex_dxf_path, output_path)

    from app.dxf.reader import collect_geometries
    from shapely.ops import unary_union
    from app.geometry.validation import fix_geometry

    doc = read_dxf(complex_dxf_path)
    comm_geoms = collect_geometries(doc, config.layers.communications)
    buffer_dist = config.get_communication_buffer()
    buffers = [create_buffer(g, buffer_dist) for g in comm_geoms]
    valid = [b for b in buffers if b is not None]
    forbidden = fix_geometry(unary_union(valid))

    for planting in result.accepted_plantings:
        pt = Point(planting.x, planting.y)
        if forbidden is not None:
            assert not forbidden.contains(pt)


def test_complex_interpretation_complete(complex_dxf_path: Path, output_dir: Path) -> None:
    output_path = output_dir / "complex_result.dxf"
    run_pipeline(complex_dxf_path, output_path)

    with open(output_dir / "interpretation.json") as f:
        data = json.load(f)

    assert len(data["plantings"]) > 0
    for p in data["plantings"]:
        assert p["id"]
        assert p["type"]
        assert "x" in p and "y" in p
        assert p["status"] == "accepted"
        assert len(p["checks"]) > 0
        assert p["explanation"]
        assert "distances" in p
        for check in p["checks"]:
            assert check["regulation"]
            assert check["clause"]
