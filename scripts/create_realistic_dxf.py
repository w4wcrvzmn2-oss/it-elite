#!/usr/bin/env python3
"""Create a realistic urban courtyard DXF resembling competition geobase.

Typical Moscow/St.Petersburg residential block (~260×200 m):
- Irregular site boundary with survey-style coordinates
- 5 building wings around central courtyard
- Playground and parking as obstacles
- Underground utilities: water, gas, heat, sewer, electric
- Street frontages on south and west
- Russian layer naming and annotation labels
"""

from __future__ import annotations

from pathlib import Path

import ezdxf
from ezdxf.enums import TextEntityAlignment


def _add_layer(doc: ezdxf.document.Drawing, name: str, color: int) -> None:
    if name not in doc.layers:
        doc.layers.add(name, color=color)


def _rect(msp, pts: list[tuple[float, float]], layer: str, close: bool = True) -> None:
    msp.add_lwpolyline(pts, close=close, dxfattribs={"layer": layer})


def _label(msp, text: str, x: float, y: float, height: float = 1.2) -> None:
    msp.add_text(
        text,
        dxfattribs={"layer": "ANNOTATIONS", "height": height},
    ).set_placement((x, y), align=TextEntityAlignment.LEFT)


def create_realistic_dxf(output_path: Path) -> None:
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 6  # meters
    doc.header["$LUPREC"] = 2

    layers = {
        "SITE": 3,
        "BUILDINGS": 8,
        "ROADS": 252,
        "WATER": 5,
        "GAS": 2,
        "PIPE": 30,
        "ELECTRIC": 1,
        "HEAT": 6,
        "ANNOTATIONS": 7,
        "EXISTING_TREES": 94,
    }
    for name, color in layers.items():
        _add_layer(doc, name, color)

    msp = doc.modelspace()

    # --- Site boundary (slightly irregular survey polygon) ---
    site = [
        (0.00, 0.00),
        (262.40, 0.35),
        (261.85, 198.72),
        (1.12, 200.00),
        (0.00, 198.50),
    ]
    _rect(msp, site, "SITE")
    _label(msp, "Граница участка благоустройства", 8, 202, 1.4)

    # --- Building wings (5-section courtyard block) ---
    # North bar (корпус 1+2)
    _rect(msp, [(18, 172), (245, 172), (245, 198), (18, 198)], "BUILDINGS")
    _label(msp, "Корпус 1-2", 110, 185)

    # South bar (корпус 5)
    _rect(msp, [(18, 2), (245, 2), (245, 28), (18, 28)], "BUILDINGS")
    _label(msp, "Корпус 5", 115, 12)

    # West wing (корпус 4)
    _rect(msp, [(2, 28), (18, 28), (18, 172), (2, 172)], "BUILDINGS")
    _label(msp, "Корпус 4", 4, 95, 1.0)

    # East wing (корпус 3)
    _rect(msp, [(245, 28), (261, 28), (261, 172), (245, 172)], "BUILDINGS")
    _label(msp, "Корпус 3", 247, 95, 1.0)

    # Transformer substation (small building)
    _rect(msp, [(230, 155), (252, 155), (252, 168), (230, 168)], "BUILDINGS")
    _label(msp, "ТП-47", 232, 160, 0.9)

    # Playground — hard obstacle
    _rect(msp, [(95, 75), (165, 75), (165, 125), (95, 125)], "BUILDINGS")
    _label(msp, "Детская площадка", 102, 98, 1.0)

    # --- Roads / frontages ---
    msp.add_line((-12, -6), (275, -6), dxfattribs={"layer": "ROADS"})
    msp.add_line((-12, -6), (-12, 205), dxfattribs={"layer": "ROADS"})
    msp.add_line((18, 2), (245, 2), dxfattribs={"layer": "ROADS"})  # internal driveway
    _label(msp, "ул. Садовая", 100, -10, 1.3)
    _label(msp, "ул. Лесная", -18, 90, 1.3)

    # Parking strip along south courtyard edge
    _rect(msp, [(30, 30), (230, 30), (230, 48), (30, 48)], "ROADS")
    _label(msp, "Парковка", 120, 36, 1.0)

    # --- Underground utilities (typical routing) ---

    # Water main — enters from south street, runs to courtyard center
    msp.add_line((131, -6), (131, 28), dxfattribs={"layer": "WATER"})
    msp.add_line((131, 28), (131, 172), dxfattribs={"layer": "WATER"})
    msp.add_line((131, 90), (220, 90), dxfattribs={"layer": "WATER"})
    _label(msp, "Водопровод Ø200", 133, 92, 0.9)

    # Heat network — along north of south building
    msp.add_line((25, 32), (240, 32), dxfattribs={"layer": "HEAT"})
    msp.add_line((25, 32), (25, 165), dxfattribs={"layer": "HEAT"})
    _label(msp, "Теплосеть", 28, 35, 0.9)

    # Gas — west side routing
    msp.add_line((8, 40), (8, 160), dxfattribs={"layer": "GAS"})
    msp.add_line((8, 100), (95, 100), dxfattribs={"layer": "GAS"})
    _label(msp, "Газопровод", 10, 102, 0.9)

    # Sewer / pressure pipeline — diagonal collector
    msp.add_line((35, 55), (220, 145), dxfattribs={"layer": "PIPE"})
    msp.add_line((35, 55), (35, 160), dxfattribs={"layer": "PIPE"})
    _label(msp, "Канализация / коллектор", 40, 58, 0.9)

    # Electric cable — from TP to courtyard
    msp.add_line((240, 161), (200, 130), dxfattribs={"layer": "ELECTRIC"})
    msp.add_line((200, 130), (165, 130), dxfattribs={"layer": "ELECTRIC"})
    _label(msp, "Кабель 0.4 кВ", 202, 132, 0.9)

    # --- Existing trees (reference, not planting output) ---
    existing = [
        (50, 140), (70, 155), (190, 140), (210, 155),
        (55, 60), (200, 60), (130, 165),
    ]
    for x, y in existing:
        msp.add_circle((x, y), 1.2, dxfattribs={"layer": "EXISTING_TREES"})
    _label(msp, "Сущ. деревья", 50, 148, 0.8)

    # --- Dimension-style ticks on boundary ---
    for x in (0, 131, 262):
        msp.add_line((x, -2), (x, 2), dxfattribs={"layer": "ANNOTATIONS"})
    for y in (0, 100, 200):
        msp.add_line((-2, y), (2, y), dxfattribs={"layer": "ANNOTATIONS"})

    _label(msp, "М 1:500 | urban_courtyard_block.dxf", 8, -16, 1.0)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(output_path))
    print(f"Created realistic DXF: {output_path} ({output_path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    create_realistic_dxf(root / "data" / "input" / "urban_courtyard_block.dxf")
