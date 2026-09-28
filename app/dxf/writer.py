"""DXF file writer for planting output."""

from __future__ import annotations

import logging
from pathlib import Path

import ezdxf

from app.config import AppConfig
from app.planting.models import PlantingPoint

logger = logging.getLogger(__name__)


class DxfWriteError(Exception):
    """Raised when DXF cannot be written."""


def write_planting_dxf(
    source_path: str | Path,
    output_path: str | Path,
    plantings: list[PlantingPoint],
    config: AppConfig,
) -> None:
    """Write output DXF with original entities preserved and new planting layers added."""
    source_path = Path(source_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        doc = ezdxf.readfile(str(source_path))
    except Exception as e:
        raise DxfWriteError(f"Cannot read source DXF: {e}") from e

    _ensure_layers(doc, config)

    msp = doc.modelspace()
    for planting in plantings:
        layer = _layer_for_type(planting.planting_type, config)
        radius = config.get_planting_config(planting.planting_type).symbol_radius

        msp.add_circle(
            center=(planting.x, planting.y),
            radius=radius,
            dxfattribs={"layer": layer, "color": _color_for_type(planting.planting_type)},
        )
        msp.add_point(
            (planting.x, planting.y),
            dxfattribs={"layer": config.output.planting_layer},
        )

    try:
        doc.saveas(str(output_path))
    except Exception as e:
        raise DxfWriteError(f"Cannot write output DXF: {e}") from e

    logger.info("Written %d plantings to %s", len(plantings), output_path)


def _ensure_layers(doc: ezdxf.document.Drawing, config: AppConfig) -> None:
    layer_names = [
        config.output.planting_layer,
        config.output.tree_layer,
        config.output.shrub_layer,
        config.output.debug_layer,
    ]
    for name in layer_names:
        if name not in doc.layers:
            doc.layers.add(name)


def _layer_for_type(planting_type: str, config: AppConfig) -> str:
    if planting_type == "tree":
        return config.output.tree_layer
    if planting_type == "shrub":
        return config.output.shrub_layer
    return config.output.planting_layer


def _color_for_type(planting_type: str) -> int:
    if planting_type == "tree":
        return 3  # green
    if planting_type == "shrub":
        return 94  # light green
    return 7


def validate_output_dxf(filepath: str | Path, config: AppConfig) -> dict:
    """Validate output DXF has planting layers and entities."""
    from app.dxf.reader import read_dxf

    doc = read_dxf(filepath)
    planting_layers = {
        config.output.planting_layer,
        config.output.tree_layer,
        config.output.shrub_layer,
    }

    found_plantings = 0
    layer_counts: dict[str, int] = {}

    for obj in doc.objects:
        layer_counts[obj.layer] = layer_counts.get(obj.layer, 0) + 1
        if obj.layer in planting_layers:
            found_plantings += 1

    return {
        "valid": found_plantings > 0,
        "planting_entities": found_plantings,
        "layer_counts": layer_counts,
        "planting_layers_present": [
            layer for layer in planting_layers if layer in doc.layers
        ],
    }
