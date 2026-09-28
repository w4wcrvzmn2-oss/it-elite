"""DXF source integrity audit utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.dxf.entities import DxfDocument
from app.dxf.layers import get_source_layer_counts


PLANTING_LAYER_PREFIXES = ("PLANTING_",)


@dataclass
class SourceLayerSnapshot:
    """Snapshot of source DXF layer state before processing."""

    layer_names: list[str] = field(default_factory=list)
    entity_counts: dict[str, int] = field(default_factory=dict)
    geometry_counts: dict[str, int] = field(default_factory=dict)
    total_entities: int = 0
    total_geometries: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer_names": self.layer_names,
            "entity_counts": self.entity_counts,
            "geometry_counts": self.geometry_counts,
            "total_entities": self.total_entities,
            "total_geometries": self.total_geometries,
        }


def capture_source_snapshot(document: DxfDocument) -> SourceLayerSnapshot:
    """Capture entity and geometry counts for non-planting source layers."""
    entity_counts = get_source_layer_counts(document)
    geometry_counts: dict[str, int] = {}

    for obj in document.objects:
        if any(obj.layer.upper().startswith(p) for p in PLANTING_LAYER_PREFIXES):
            continue
        if obj.geometry is not None:
            geometry_counts[obj.layer] = geometry_counts.get(obj.layer, 0) + 1

    return SourceLayerSnapshot(
        layer_names=sorted(entity_counts.keys()),
        entity_counts=entity_counts,
        geometry_counts=geometry_counts,
        total_entities=sum(entity_counts.values()),
        total_geometries=sum(geometry_counts.values()),
    )


def compare_snapshots(
    before: SourceLayerSnapshot,
    after: SourceLayerSnapshot,
) -> list[str]:
    """Return list of differences between before/after snapshots."""
    errors: list[str] = []

    if before.layer_names != after.layer_names:
        added = set(after.layer_names) - set(before.layer_names)
        removed = set(before.layer_names) - after.layer_names
        if added:
            errors.append(f"New source layers appeared: {sorted(added)}")
        if removed:
            errors.append(f"Source layers removed: {sorted(removed)}")

    for layer, count_before in before.entity_counts.items():
        count_after = after.entity_counts.get(layer, 0)
        if count_after != count_before:
            errors.append(
                f"Layer '{layer}' entity count changed: {count_before} → {count_after}"
            )

    for layer, count_before in before.geometry_counts.items():
        count_after = after.geometry_counts.get(layer, 0)
        if count_after != count_before:
            errors.append(
                f"Layer '{layer}' geometry count changed: {count_before} → {count_after}"
            )

    return errors
