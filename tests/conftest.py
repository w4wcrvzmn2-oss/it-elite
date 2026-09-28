"""Test fixtures."""

from __future__ import annotations

from pathlib import Path

import ezdxf
import pytest

from app.config import load_config


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def config(project_root: Path):
    return load_config(project_root / "config" / "default.yaml")


@pytest.fixture
def test_dxf_path(tmp_path: Path) -> Path:
    """Create a test DXF with site boundary, pipe, building, and road."""
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # SITE boundary: 100x100 rectangle
    site_points = [(0, 0), (100, 0), (100, 100), (0, 100)]
    msp.add_lwpolyline(site_points, close=True, dxfattribs={"layer": "SITE"})

    # PIPE: horizontal line through middle
    msp.add_line((10, 50), (90, 50), dxfattribs={"layer": "PIPE"})

    # BUILDING: rectangle in corner
    building_points = [(70, 70), (95, 70), (95, 95), (70, 95)]
    msp.add_lwpolyline(building_points, close=True, dxfattribs={"layer": "BUILDINGS"})

    # ROAD: line along bottom
    msp.add_line((0, 5), (100, 5), dxfattribs={"layer": "ROADS"})

    path = tmp_path / "test.dxf"
    doc.saveas(str(path))
    return path


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    out = tmp_path / "output"
    out.mkdir()
    return out
