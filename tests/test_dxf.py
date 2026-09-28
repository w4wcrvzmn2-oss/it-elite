"""Tests for DXF reading and writing."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config import load_config
from app.dxf.layers import get_source_layer_counts
from app.dxf.reader import inspect_dxf, read_dxf
from app.dxf.writer import validate_output_dxf, write_planting_dxf
from app.planting.models import PlantingPoint
from app.pipeline import run_pipeline


def test_dxf_reader(test_dxf_path: Path) -> None:
    doc = read_dxf(test_dxf_path)
    assert doc.total_entities >= 4
    assert "SITE" in doc.layers
    assert "PIPE" in doc.layers


def test_dxf_layers(test_dxf_path: Path) -> None:
    doc = read_dxf(test_dxf_path)
    site = doc.layers["SITE"]
    assert site.number_of_entities >= 1
    assert "LWPOLYLINE" in site.entity_types


def test_dxf_inspect(test_dxf_path: Path) -> None:
    info = inspect_dxf(test_dxf_path)
    assert info["total_entities"] >= 4
    assert "SITE" in info["layers"]
    assert info["bounding_box"] is not None


def test_no_source_layer_modification(test_dxf_path: Path, output_dir: Path, config) -> None:
    output_path = output_dir / "result.dxf"
    result = run_pipeline(test_dxf_path, output_path)

    before = result.context.source_layer_counts_before
    after_doc = read_dxf(output_path)
    after = get_source_layer_counts(after_doc)

    for layer, count in before.items():
        assert after.get(layer, 0) == count, f"Layer {layer} was modified"


def test_output_layer(test_dxf_path: Path, output_dir: Path, config) -> None:
    output_path = output_dir / "result.dxf"
    run_pipeline(test_dxf_path, output_path)

    validation = validate_output_dxf(output_path, config)
    assert validation["valid"]
    assert validation["planting_entities"] > 0
    assert config.output.planting_layer in validation["planting_layers_present"] or \
           config.output.tree_layer in validation["planting_layers_present"]
