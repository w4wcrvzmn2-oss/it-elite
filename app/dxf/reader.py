"""DXF file reader."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import ezdxf
from ezdxf.document import Drawing
from ezdxf.entities import DXFEntity
from shapely.geometry import (
    LineString,
    MultiLineString,
    MultiPoint,
    Point,
    Polygon,
)

from app.dxf.entities import DxfDocument, GeometryObject
from app.dxf.layers import build_layer_info, count_entities_by_layer

logger = logging.getLogger(__name__)

SUPPORTED_TYPES = {
    "LINE",
    "LWPOLYLINE",
    "POLYLINE",
    "CIRCLE",
    "ARC",
    "POINT",
    "INSERT",
}


class DxfReadError(Exception):
    """Raised when DXF cannot be read or parsed."""


def read_dxf(filepath: str | Path) -> DxfDocument:
    """Read a DXF file and return a unified document model."""
    path = Path(filepath)
    if not path.exists():
        raise DxfReadError(f"DXF file not found: {path}")

    try:
        doc = ezdxf.readfile(str(path))
    except ezdxf.DXFStructureError as e:
        raise DxfReadError(f"Corrupted or invalid DXF structure: {e}") from e
    except IOError as e:
        raise DxfReadError(f"Cannot read DXF file: {e}") from e

    objects: list[GeometryObject] = []
    msp = doc.modelspace()

    for entity in msp:
        etype = entity.dxftype()
        if etype not in SUPPORTED_TYPES:
            continue
        try:
            geom_obj = _entity_to_geometry(entity)
            if geom_obj is not None:
                objects.append(geom_obj)
        except Exception as e:
            logger.warning("Skipping entity %s (%s): %s", entity.dxf.handle, etype, e)

    layers = build_layer_info(objects)
    source_counts = count_entities_by_layer(
        DxfDocument(filepath=str(path), objects=objects, layers=layers)
    )

    return DxfDocument(
        filepath=str(path),
        objects=objects,
        layers=layers,
        source_entity_count=source_counts,
    )


def _entity_to_geometry(entity: DXFEntity) -> GeometryObject | None:
    etype = entity.dxftype()
    handle = str(entity.dxf.handle)
    layer = entity.dxf.layer
    metadata: dict[str, Any] = {"handle": handle, "dxf_type": etype}

    geometry = None

    if etype == "LINE":
        geometry = LineString(
            [(entity.dxf.start.x, entity.dxf.start.y), (entity.dxf.end.x, entity.dxf.end.y)]
        )
    elif etype == "LWPOLYLINE":
        points = [(p[0], p[1]) for p in entity.get_points(format="xy")]
        if len(points) >= 2:
            if entity.closed and len(points) >= 3:
                geometry = Polygon(points)
            else:
                geometry = LineString(points)
    elif etype == "POLYLINE":
        points = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
        if len(points) >= 2:
            if entity.is_closed and len(points) >= 3:
                geometry = Polygon(points)
            else:
                geometry = LineString(points)
    elif etype == "CIRCLE":
        center = (entity.dxf.center.x, entity.dxf.center.y)
        geometry = Point(center).buffer(entity.dxf.radius, quad_segs=32)
        metadata["radius"] = entity.dxf.radius
        metadata["center"] = center
    elif etype == "ARC":
        center = (entity.dxf.center.x, entity.dxf.center.y)
        geometry = Point(center).buffer(entity.dxf.radius, quad_segs=32)
        metadata["radius"] = entity.dxf.radius
        metadata["center"] = center
        metadata["start_angle"] = entity.dxf.start_angle
        metadata["end_angle"] = entity.dxf.end_angle
    elif etype == "POINT":
        geometry = Point(entity.dxf.location.x, entity.dxf.location.y)
    elif etype == "INSERT":
        geometry = Point(entity.dxf.insert.x, entity.dxf.insert.y)
        metadata["block_name"] = entity.dxf.name

    return GeometryObject(
        id=handle,
        layer=layer,
        type=etype,
        geometry=geometry,
        metadata=metadata,
    )


_INSUNITS_NAMES: dict[int, str] = {
    0: "unitless",
    1: "inches",
    2: "feet",
    3: "miles",
    4: "millimeters",
    5: "centimeters",
    6: "meters",
    7: "kilometers",
    8: "microinches",
    9: "mils",
    10: "yards",
    11: "angstroms",
    12: "nanometers",
    13: "microns",
    14: "decimeters",
    15: "decameters",
    16: "hectometers",
    17: "gigameters",
    18: "astronomical units",
    19: "light years",
    20: "parsecs",
}


def _read_dxf_units(filepath: Path) -> dict[str, Any]:
    """Read units and scale hints from DXF header."""
    try:
        raw = ezdxf.readfile(str(filepath))
    except Exception:
        return {"insunits": None, "units_name": "unknown", "measurement": None}

    header = raw.header
    insunits = header.get("$INSUNITS", 0)
    measurement = header.get("$MEASUREMENT", None)
    units_name = _INSUNITS_NAMES.get(int(insunits), f"code_{insunits}")

    scale_hint = "assumed_meters"
    if insunits in (4, 5, 6):
        scale_hint = "metric"
    elif insunits in (1, 2):
        scale_hint = "imperial"
    elif insunits == 0:
        scale_hint = "unitless_assumed_meters"

    return {
        "insunits": int(insunits),
        "units_name": units_name,
        "measurement": int(measurement) if measurement is not None else None,
        "scale_hint": scale_hint,
    }


def inspect_dxf(filepath: str | Path) -> dict[str, Any]:
    """Inspect DXF file and return summary information."""
    path = Path(filepath)
    doc = read_dxf(path)
    file_size = path.stat().st_size
    units_info = _read_dxf_units(path)

    all_types: set[str] = set()
    global_bbox: list[float] | None = None

    for layer_info in doc.layers.values():
        all_types.update(layer_info.entity_types)
        if layer_info.bounding_box:
            if global_bbox is None:
                global_bbox = list(layer_info.bounding_box)
            else:
                global_bbox[0] = min(global_bbox[0], layer_info.bounding_box[0])
                global_bbox[1] = min(global_bbox[1], layer_info.bounding_box[1])
                global_bbox[2] = max(global_bbox[2], layer_info.bounding_box[2])
                global_bbox[3] = max(global_bbox[3], layer_info.bounding_box[3])

    width = height = None
    if global_bbox:
        width = round(global_bbox[2] - global_bbox[0], 2)
        height = round(global_bbox[3] - global_bbox[1], 2)

    return {
        "filepath": str(path),
        "file_size_bytes": file_size,
        "total_entities": doc.total_entities,
        "entity_types": sorted(all_types),
        "bounding_box": tuple(global_bbox) if global_bbox else None,
        "extent_width": width,
        "extent_height": height,
        "units": units_info,
        "layers": {
            name: {
                "number_of_entities": info.number_of_entities,
                "entity_types": info.entity_types,
                "bounding_box": info.bounding_box,
            }
            for name, info in sorted(doc.layers.items())
        },
    }


def collect_geometries(
    document: DxfDocument, layer_names: list[str]
) -> list[Any]:
    """Collect shapely geometries from specified layers."""
    geoms = []
    upper = {n.upper() for n in layer_names}
    for obj in document.objects:
        if obj.layer.upper() in upper and obj.geometry is not None:
            geoms.append(obj.geometry)
    return geoms
