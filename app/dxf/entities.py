"""Unified geometry object model for DXF entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shapely.geometry.base import BaseGeometry


@dataclass
class GeometryObject:
    """Unified internal representation of a DXF entity."""

    id: str
    layer: str
    type: str
    geometry: BaseGeometry | None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LayerInfo:
    """Summary information about a DXF layer."""

    layer_name: str
    number_of_entities: int
    entity_types: list[str]
    bounding_box: tuple[float, float, float, float] | None


@dataclass
class DxfDocument:
    """Parsed DXF document with geometry objects and layer metadata."""

    filepath: str
    objects: list[GeometryObject]
    layers: dict[str, LayerInfo]
    source_entity_count: dict[str, int] = field(default_factory=dict)

    @property
    def total_entities(self) -> int:
        return len(self.objects)

    def entities_by_layer(self, layer_name: str) -> list[GeometryObject]:
        return [o for o in self.objects if o.layer.upper() == layer_name.upper()]

    def entities_by_category(
        self, layer_names: list[str]
    ) -> list[GeometryObject]:
        upper_names = {n.upper() for n in layer_names}
        return [o for o in self.objects if o.layer.upper() in upper_names]
