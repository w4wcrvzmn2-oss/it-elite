"""Generate plan snapshots and optional AI-enhanced visualizations."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.plotting import plot_polygon

from app.config import load_config
from app.dxf.reader import read_dxf
from app.pipeline import PipelineContext, _classify_and_build_geometry
from app.planting.models import PlantingPoint
from app.visualization.image_gen import VIZ_PROMPTS, generate_ai_image

logger = logging.getLogger(__name__)

VIZ_TYPES = [
    ("overview", "Общий вид участка", 14, 10),
    ("pedestrian", "Перспектива с уровня человека", 10, 8),
    ("detail", "Детальный вид озеленённой зоны", 8, 8),
]

PLAN_BADGE = "Инженерный план · Green Planner"
AI_BADGE = "AI-визуализация · Основано на рассчитанном плане Green Planner"


def _render_plan(
    ctx: PipelineContext,
    plantings: list[PlantingPoint],
    output_path: Path,
    title: str,
    figsize: tuple[int, int],
    zoom: float = 1.0,
) -> None:
    fig, ax = plt.subplots(1, 1, figsize=figsize, dpi=120)
    if ctx.planting_boundary is not None:
        plot_polygon(ctx.planting_boundary, ax=ax, add_points=False, color="#E2E8F0", alpha=0.5)
    if ctx.forbidden_zone is not None:
        plot_polygon(ctx.forbidden_zone, ax=ax, add_points=False, color="#FECACA", alpha=0.45)
    if ctx.allowed_area is not None:
        plot_polygon(ctx.allowed_area, ax=ax, add_points=False, color="#BBF7D0", alpha=0.35)

    colors = {"communications": "#2563EB", "buildings": "#78716C", "roads": "#64748B"}
    for category, geoms in ctx.restriction_geometries.items():
        color = colors.get(category, "#94A3B8")
        for geom in geoms:
            if geom.geom_type == "LineString":
                xs, ys = geom.xy
                ax.plot(xs, ys, color=color, linewidth=1.2, alpha=0.8)
            elif geom.geom_type == "Polygon":
                plot_polygon(geom, ax=ax, add_points=False, color=color, alpha=0.4)

    trees = [p for p in plantings if p.planting_type == "tree"]
    shrubs = [p for p in plantings if p.planting_type == "shrub"]
    if shrubs:
        ax.scatter([p.x for p in shrubs], [p.y for p in shrubs], s=8, c="#4ADE80", alpha=0.6, zorder=5)
    if trees:
        ax.scatter([p.x for p in trees], [p.y for p in trees], s=28, c="#15803D", alpha=0.85, zorder=6)

    ax.set_aspect("equal")
    ax.set_title(title, fontsize=11, pad=10)
    ax.grid(True, alpha=0.2)
    if ctx.planting_boundary is not None and zoom != 1.0:
        minx, miny, maxx, maxy = ctx.planting_boundary.bounds
        cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
        w, h = (maxx - minx) / zoom, (maxy - miny) / zoom
        ax.set_xlim(cx - w / 2, cx + w / 2)
        ax.set_ylim(cy - h / 2, cy + h / 2)

    fig.text(0.5, 0.02, PLAN_BADGE, ha="center", fontsize=7, color="#64748B")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(output_path, format="png", facecolor="white")
    plt.close(fig)


def _build_description(run_report: dict, plantings: list[PlantingPoint]) -> dict:
    types = run_report.get("planting_types", {})
    return {
        "scene": "городской двор / участок благоустройства",
        "trees": types.get("tree", 0),
        "shrubs": types.get("shrub", 0),
        "allowed_area_m2": run_report.get("allowed_area_m2"),
        "site_area_m2": run_report.get("site_area_m2"),
        "density": run_report.get("density_per_1000m2"),
        "note": "Сохранить пространственную структуру участка. Не перемещать здания и дороги.",
    }


def generate_visualizations(
    input_path: Path,
    output_dir: Path,
    run_report: dict,
    plantings: list[PlantingPoint],
    config_path: Path | None = None,
) -> list[dict]:
    if os.getenv("VISUALIZATION_ENABLED", "true").lower() not in ("1", "true", "yes"):
        return []

    viz_dir = output_dir / "visualizations"
    viz_dir.mkdir(parents=True, exist_ok=True)

    config = load_config(config_path or (output_dir / "config.yaml"))
    ctx = PipelineContext()
    ctx.document = read_dxf(input_path)
    _classify_and_build_geometry(ctx, config)

    desc = _build_description(run_report, plantings)
    (viz_dir / "description.json").write_text(
        json.dumps(desc, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    zooms = {"overview": 1.0, "pedestrian": 1.8, "detail": 2.5}
    results: list[dict] = []
    ai_enabled = bool(os.getenv("OPENROUTER_IMAGE_MODEL", "").strip())

    for viz_id, title, w, h in VIZ_TYPES:
        plan_path = viz_dir / f"plan_{viz_id}.png"
        _render_plan(ctx, plantings, plan_path, title, (w, h), zoom=zooms[viz_id])
        results.append({
            "id": f"plan_{viz_id}",
            "viz_type": viz_id,
            "kind": "plan",
            "title": f"{title} (план)",
            "filename": plan_path.name,
            "created_at": datetime.utcnow().isoformat(),
            "model": "matplotlib",
            "ai_generated": False,
            "badge": PLAN_BADGE,
        })

        if ai_enabled:
            prompt_tpl = VIZ_PROMPTS.get(viz_id, VIZ_PROMPTS["overview"])
            prompt = prompt_tpl.format(trees=desc["trees"], shrubs=desc["shrubs"])
            img_bytes, model = generate_ai_image(prompt)
            if img_bytes:
                ai_path = viz_dir / f"ai_{viz_id}.png"
                ai_path.write_bytes(img_bytes)
                results.append({
                    "id": f"ai_{viz_id}",
                    "viz_type": viz_id,
                    "kind": "ai",
                    "title": title,
                    "filename": ai_path.name,
                    "created_at": datetime.utcnow().isoformat(),
                    "model": model,
                    "ai_generated": True,
                    "badge": AI_BADGE,
                })
            else:
                logger.warning("AI image skipped for %s (fallback to plan only)", viz_id)

    meta_path = viz_dir / "manifest.json"
    meta_path.write_text(json.dumps({"visualizations": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    return results


def list_visualizations(output_dir: Path) -> list[dict]:
    manifest = output_dir / "visualizations" / "manifest.json"
    if manifest.exists():
        with open(manifest) as f:
            return json.load(f).get("visualizations", [])
    return []
