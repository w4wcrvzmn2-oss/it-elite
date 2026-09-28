#!/usr/bin/env python3
"""Create a test DXF fixture for demo and Docker testing."""

from pathlib import Path

import ezdxf


def create_test_dxf(output_path: Path) -> None:
    doc = ezdxf.new("R2010")

    for layer in ("SITE", "PIPE", "BUILDINGS", "ROADS"):
        if layer not in doc.layers:
            doc.layers.add(layer)

    msp = doc.modelspace()

    # SITE: 100x100
    msp.add_lwpolyline(
        [(0, 0), (100, 0), (100, 100), (0, 100)],
        close=True,
        dxfattribs={"layer": "SITE"},
    )

    # PIPE: horizontal through center
    msp.add_line((10, 50), (90, 50), dxfattribs={"layer": "PIPE"})

    # BUILDING
    msp.add_lwpolyline(
        [(70, 70), (95, 70), (95, 95), (70, 95)],
        close=True,
        dxfattribs={"layer": "BUILDINGS"},
    )

    # ROAD
    msp.add_line((0, 5), (100, 5), dxfattribs={"layer": "ROADS"})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(output_path))
    print(f"Created test DXF: {output_path}")


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    create_test_dxf(root / "data" / "input" / "test.dxf")
