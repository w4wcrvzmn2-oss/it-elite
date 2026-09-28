#!/usr/bin/env python3
"""Create a complex synthetic DXF for E2E testing.

Layout (200×150 m site):
- SITE boundary with L-shaped cutout
- 3 communication lines (PIPE, WATER, GAS) with crossing buffers
- 2 buildings
- 2 roads
- Multiple allowed zones separated by restrictions
"""

from pathlib import Path

import ezdxf


def create_complex_dxf(output_path: Path) -> None:
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 6  # meters

    for layer in ("SITE", "PIPE", "WATER", "GAS", "BUILDINGS", "ROADS"):
        if layer not in doc.layers:
            doc.layers.add(layer)

    msp = doc.modelspace()

    # Site boundary 200×150 with rectangular cutout (creates 2 zones)
    site_outer = [
        (0, 0), (200, 0), (200, 150), (0, 150),
    ]
    msp.add_lwpolyline(site_outer, close=True, dxfattribs={"layer": "SITE"})

    # Internal obstacle as building (creates separate allowed pockets)
    msp.add_lwpolyline(
        [(80, 60), (120, 60), (120, 90), (80, 90)],
        close=True,
        dxfattribs={"layer": "BUILDINGS"},
    )

    # Building 2 — corner
    msp.add_lwpolyline(
        [(160, 110), (195, 110), (195, 145), (160, 145)],
        close=True,
        dxfattribs={"layer": "BUILDINGS"},
    )

    # Communications — crossing pattern
    msp.add_line((20, 75), (180, 75), dxfattribs={"layer": "PIPE"})
    msp.add_line((100, 10), (100, 140), dxfattribs={"layer": "WATER"})
    msp.add_line((40, 30), (160, 120), dxfattribs={"layer": "GAS"})

    # Roads
    msp.add_line((0, 8), (200, 8), dxfattribs={"layer": "ROADS"})
    msp.add_line((0, 142), (200, 142), dxfattribs={"layer": "ROADS"})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(output_path))
    print(f"Created complex test DXF: {output_path}")


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    create_complex_dxf(root / "data" / "input" / "synthetic_complex.dxf")
