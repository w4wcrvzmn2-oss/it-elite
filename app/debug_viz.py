"""Debug visualization for planting pipeline."""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection
from shapely.geometry import Point
from shapely.plotting import plot_polygon, plot_points

from app.config import load_config
from app.pipeline import PipelineContext, _classify_and_build_geometry
from app.dxf.reader import read_dxf
from app.planting.generator import generate_candidates
from app.planting.optimizer import optimize_placements
from app.rules.engine import RulesEngine
from app.rules.loader import load_rules_from_config

logger = logging.getLogger(__name__)


def generate_debug_map(
    input_path: Path,
    output_path: Path,
    config_path: Path | None = None,
) -> None:
    """Generate debug visualization PNG."""
    config = load_config(config_path)
    ctx = PipelineContext()
    ctx.document = read_dxf(input_path)
    _classify_and_build_geometry(ctx, config)

    catalog = load_rules_from_config(config)
    rules_engine = RulesEngine(catalog, ctx.restriction_geometries)

    fig, ax = plt.subplots(1, 1, figsize=(14, 10))

    if ctx.planting_boundary is not None:
        plot_polygon(ctx.planting_boundary, ax=ax, add_points=False, color="lightgray", alpha=0.3)

    if ctx.forbidden_zone is not None:
        plot_polygon(ctx.forbidden_zone, ax=ax, add_points=False, color="red", alpha=0.3)

    if ctx.allowed_area is not None:
        plot_polygon(ctx.allowed_area, ax=ax, add_points=False, color="lightgreen", alpha=0.2)

    colors = {"communications": "orange", "buildings": "brown", "roads": "gray"}
    for category, geoms in ctx.restriction_geometries.items():
        color = colors.get(category, "blue")
        for geom in geoms:
            if geom.geom_type in ("LineString", "MultiLineString"):
                if geom.geom_type == "LineString":
                    xs, ys = geom.xy
                    ax.plot(xs, ys, color=color, linewidth=1.5, alpha=0.8)
                else:
                    for line in geom.geoms:
                        xs, ys = line.xy
                        ax.plot(xs, ys, color=color, linewidth=1.5, alpha=0.8)
            elif geom.geom_type in ("Polygon", "MultiPolygon"):
                plot_polygon(geom, ax=ax, add_points=False, color=color, alpha=0.5)

    all_candidates: list[tuple[float, float]] = []
    all_accepted = []

    for planting_type in config.planting:
        pconfig = config.get_planting_config(planting_type)
        if not pconfig.enabled or ctx.allowed_area is None:
            continue
        candidates = generate_candidates(ctx.allowed_area, planting_type, config)
        all_candidates.extend(candidates)
        accepted, _ = optimize_placements(
            candidates,
            planting_type,
            config,
            rules_engine,
            ctx.restriction_geometries,
            ctx.allowed_area,
        )
        all_accepted.extend(accepted)

    if all_candidates:
        cx = [p[0] for p in all_candidates]
        cy = [p[1] for p in all_candidates]
        ax.scatter(cx, cy, c="yellow", s=8, alpha=0.4, marker=".", label="Candidates")

    if all_accepted:
        ax.scatter(
            [p.x for p in all_accepted],
            [p.y for p in all_accepted],
            c="green",
            s=60,
            marker="o",
            edgecolors="darkgreen",
            linewidths=1,
            label="Accepted plantings",
            zorder=5,
        )

    ax.set_aspect("equal")
    ax.legend(loc="upper right")
    ax.set_title("Green Planner Debug Map")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.grid(True, alpha=0.3)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Debug map saved to %s", output_path)
