"""Layer analysis utilities."""

from __future__ import annotations

from collections import defaultdict

from shapely.geometry.base import BaseGeometry

from app.dxf.entities import DxfDocument, GeometryObject, LayerInfo


def build_layer_info(objects: list[GeometryObject]) -> dict[str, LayerInfo]:
    """Build layer summary from geometry objects."""
    by_layer: dict[str, list[GeometryObject]] = defaultdict(list)
    for obj in objects:
        by_layer[obj.layer].append(obj)

    result: dict[str, LayerInfo] = {}
    for layer_name, layer_objects in by_layer.items():
        entity_types = sorted({o.type for o in layer_objects})
        bbox = _compute_bbox([o.geometry for o in layer_objects if o.geometry is not None])
        result[layer_name] = LayerInfo(
            layer_name=layer_name,
            number_of_entities=len(layer_objects),
            entity_types=entity_types,
            bounding_box=bbox,
        )
    return result


def _compute_bbox(
    geometries: list[BaseGeometry],
) -> tuple[float, float, float, float] | None:
    if not geometries:
        return None
    minx = min(g.bounds[0] for g in geometries)
    miny = min(g.bounds[1] for g in geometries)
    maxx = max(g.bounds[2] for g in geometries)
    maxy = max(g.bounds[3] for g in geometries)
    return (minx, miny, maxx, maxy)


def count_entities_by_layer(document: DxfDocument) -> dict[str, int]:
    """Count entities per layer."""
    counts: dict[str, int] = defaultdict(int)
    for obj in document.objects:
        counts[obj.layer] += 1
    return dict(counts)


def get_source_layer_counts(document: DxfDocument) -> dict[str, int]:
    """Get entity counts for source layers (excluding planting output layers)."""
    planting_prefixes = ("PLANTING_",)
    counts: dict[str, int] = defaultdict(int)
    for obj in document.objects:
        if not any(obj.layer.upper().startswith(p) for p in planting_prefixes):
            counts[obj.layer] += 1
    return dict(counts)
