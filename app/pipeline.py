"""Main processing pipeline."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from shapely.geometry.base import BaseGeometry

from app.config import AppConfig, load_config
from app.dxf.audit import capture_source_snapshot, compare_snapshots
from app.dxf.entities import DxfDocument
from app.dxf.layers import get_source_layer_counts
from app.dxf.reader import collect_geometries, read_dxf
from app.dxf.writer import write_planting_dxf
from app.geometry.buffers import (
    calculate_allowed_area,
    create_forbidden_zone,
    get_planting_boundary,
)
from app.geometry.validation import safe_area
from app.interpretation.generator import generate_interpretation, save_interpretation
from app.planting.generator import generate_candidates
from app.planting.models import PlantingPoint, RejectedPoint
from app.planting.optimizer import optimize_placements
from app.planting.validator import validate_all_plantings
from app.rules.engine import RulesEngine
from app.rules.loader import load_default_rules_json, load_rules_from_config

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Raised when pipeline processing fails."""


@dataclass
class PipelineContext:
    """Intermediate state during pipeline execution."""

    document: DxfDocument | None = None
    planting_boundary: BaseGeometry | None = None
    restriction_geometries: dict[str, list[BaseGeometry]] = field(default_factory=dict)
    forbidden_zone: BaseGeometry | None = None
    allowed_area: BaseGeometry | None = None
    candidates: dict[str, list[tuple[float, float]]] = field(default_factory=dict)
    accepted: list[PlantingPoint] = field(default_factory=list)
    rejected: list[RejectedPoint] = field(default_factory=list)
    source_layer_counts_before: dict[str, int] = field(default_factory=dict)
    source_snapshot_before: object | None = None


@dataclass
class PipelineResult:
    """Final pipeline result."""

    output_dxf: Path
    interpretation_json: Path
    run_report_json: Path
    accepted_plantings: list[PlantingPoint]
    rejected_plantings: list[RejectedPoint]
    processing_time_sec: float
    context: PipelineContext


def run_pipeline(
    input_path: Path,
    output_path: Path,
    config_path: Path | None = None,
) -> PipelineResult:
    """Execute the full planting pipeline."""
    start_time = time.time()
    config = load_config(config_path)
    ctx = PipelineContext()

    logger.info("Reading DXF: %s", input_path)
    ctx.document = read_dxf(input_path)
    ctx.source_snapshot_before = capture_source_snapshot(ctx.document)
    ctx.source_layer_counts_before = ctx.source_snapshot_before.entity_counts

    _classify_and_build_geometry(ctx, config)
    catalog = load_rules_from_config(config)
    rules_engine = RulesEngine(catalog, ctx.restriction_geometries)

    all_accepted: list[PlantingPoint] = []
    all_rejected: list[RejectedPoint] = []
    total_candidates = 0
    planting_index = 0

    for planting_type in config.planting:
        pconfig = config.get_planting_config(planting_type)
        if not pconfig.enabled:
            continue

        if ctx.allowed_area is None:
            logger.warning("No allowed area for %s planting", planting_type)
            continue

        candidates = generate_candidates(ctx.allowed_area, planting_type, config)
        ctx.candidates[planting_type] = candidates
        total_candidates += len(candidates)

        accepted, rejected = optimize_placements(
            candidates,
            planting_type,
            config,
            rules_engine,
            ctx.restriction_geometries,
            ctx.allowed_area,
            start_index=planting_index,
        )
        planting_index += len(accepted)
        all_accepted.extend(accepted)
        all_rejected.extend(rejected)

    if ctx.allowed_area is not None:
        all_accepted = validate_all_plantings(
            all_accepted, ctx.allowed_area, rules_engine, config
        )

    logger.info("Writing output DXF: %s", output_path)
    write_planting_dxf(input_path, output_path, all_accepted, config)

    _verify_source_layers_preserved(output_path, ctx.source_snapshot_before)

    output_dir = output_path.parent
    interpretation_path = output_dir / "interpretation.json"
    run_report_path = output_dir / "run_report.json"

    type_counts: dict[str, int] = {}
    for p in all_accepted:
        type_counts[p.planting_type] = type_counts.get(p.planting_type, 0) + 1

    processing_time = time.time() - start_time

    summary = {
        "input_file": str(input_path),
        "processing_time_sec": round(processing_time, 2),
        "allowed_area": safe_area(ctx.allowed_area),
        "forbidden_area": safe_area(ctx.forbidden_zone),
    }

    report = generate_interpretation(all_accepted, all_rejected, catalog, summary)
    save_interpretation(report, interpretation_path)

    run_report = _build_run_report(
        input_path=input_path,
        output_path=output_path,
        ctx=ctx,
        config=config,
        total_candidates=total_candidates,
        accepted=all_accepted,
        rejected=all_rejected,
        processing_time=processing_time,
        type_counts=type_counts,
        catalog=catalog,
    )
    run_report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(run_report_path, "w", encoding="utf-8") as f:
        json.dump(run_report, f, ensure_ascii=False, indent=2)

    logger.info(
        "Pipeline complete: %d accepted, %d rejected in %.2fs",
        len(all_accepted),
        len(all_rejected),
        processing_time,
    )

    return PipelineResult(
        output_dxf=output_path,
        interpretation_json=interpretation_path,
        run_report_json=run_report_path,
        accepted_plantings=all_accepted,
        rejected_plantings=all_rejected,
        processing_time_sec=processing_time,
        context=ctx,
    )


def _classify_and_build_geometry(ctx: PipelineContext, config: AppConfig) -> None:
    """Classify layers and build geometric constraints."""
    assert ctx.document is not None
    doc = ctx.document

    layer_mapping = config.layers
    classified: dict[str, list[str]] = {
        "communications": layer_mapping.communications,
        "buildings": layer_mapping.buildings,
        "roads": layer_mapping.roads,
        "boundary": layer_mapping.boundary,
    }

    detected_layers = set(doc.layers.keys())
    found_categories: dict[str, list[str]] = {}

    for category, configured_names in classified.items():
        matched = []
        for layer_name in detected_layers:
            for pattern in configured_names:
                if layer_name.upper() == pattern.upper() or pattern.upper() in layer_name.upper():
                    matched.append(layer_name)
                    break
        found_categories[category] = matched

    if not found_categories.get("communications"):
        available = sorted(detected_layers)
        raise PipelineError(
            "No communication layers were detected.\n\n"
            f"Detected layers:\n"
            + "\n".join(f"- {l}" for l in available)
            + "\n\nPlease configure communication layers in config/default.yaml."
        )

    if not found_categories.get("boundary"):
        logger.warning(
            "No boundary layer detected, using convex hull of all geometries as fallback"
        )

    ctx.restriction_geometries = {}
    for category in ("communications", "buildings", "roads"):
        geoms = collect_geometries(doc, found_categories.get(category, []))
        ctx.restriction_geometries[category] = geoms
        logger.info("Category %s: %d geometries from layers %s",
                     category, len(geoms), found_categories.get(category, []))

    boundary_geoms = collect_geometries(doc, found_categories.get("boundary", []))
    all_geoms = [o.geometry for o in doc.objects if o.geometry is not None]
    ctx.planting_boundary = get_planting_boundary(boundary_geoms, all_geoms)

    if ctx.planting_boundary is None:
        raise PipelineError(
            "Cannot determine planting boundary. "
            "Please configure boundary layers in config/default.yaml."
        )

    buffer_distances: dict[str, float] = {
        "communications": config.get_communication_buffer(),
    }
    for planting_type in config.planting:
        type_rules = config.get_type_rules(planting_type)
        if type_rules.building:
            buffer_distances["buildings"] = max(
                buffer_distances.get("buildings", 0),
                type_rules.building.minimum_distance,
            )
        if type_rules.road:
            buffer_distances["roads"] = max(
                buffer_distances.get("roads", 0),
                type_rules.road.minimum_distance,
            )

    ctx.forbidden_zone, _ = create_forbidden_zone(
        ctx.restriction_geometries, buffer_distances
    )
    ctx.allowed_area = calculate_allowed_area(ctx.planting_boundary, ctx.forbidden_zone)

    allowed = safe_area(ctx.allowed_area)
    if allowed <= 0:
        raise PipelineError(
            f"Allowed planting area is too small ({allowed:.1f} m²). "
            "Check boundary and restriction configuration."
        )

    logger.info(
        "Allowed area: %.1f m², Forbidden area: %.1f m²",
        allowed,
        safe_area(ctx.forbidden_zone),
    )


def _verify_source_layers_preserved(
    output_path: Path,
    snapshot_before,
) -> None:
    """Verify source layer entity and geometry counts are preserved."""
    output_doc = read_dxf(output_path)
    snapshot_after = capture_source_snapshot(output_doc)
    errors = compare_snapshots(snapshot_before, snapshot_after)
    if errors:
        raise PipelineError(
            "Source DXF layers were modified during processing:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )


def _build_run_report(
    input_path: Path,
    output_path: Path,
    ctx: PipelineContext,
    config: AppConfig,
    total_candidates: int,
    accepted: list[PlantingPoint],
    rejected: list[RejectedPoint],
    processing_time: float,
    type_counts: dict[str, int],
    catalog,
) -> dict:
    """Build run report dictionary."""
    assert ctx.document is not None
    comm_count = len(ctx.restriction_geometries.get("communications", []))

    default_rules = load_default_rules_json()

    site_area = round(safe_area(ctx.planting_boundary), 1)
    forbidden_area = round(safe_area(ctx.forbidden_zone), 1)
    allowed_area = round(safe_area(ctx.allowed_area), 1)
    planting_count = len(accepted)
    density_per_1000m2 = (
        round(planting_count / allowed_area * 1000, 2) if allowed_area > 0 else 0.0
    )

    planting_config_report: dict[str, dict] = {}
    for ptype, pcfg in config.planting.items():
        planting_config_report[ptype] = {
            "min_spacing": pcfg.min_spacing,
            "max_count": pcfg.max_count,
            "target_density": pcfg.target_density,
            "enabled": pcfg.enabled,
            "accepted_count": type_counts.get(ptype, 0),
        }

    return {
        "input_file": str(input_path),
        "output_file": str(output_path),
        "processing_time_sec": round(processing_time, 2),
        "input_entities": ctx.document.total_entities,
        "communications": comm_count,
        "site_area_m2": site_area,
        "forbidden_area_m2": forbidden_area,
        "allowed_area_m2": allowed_area,
        "forbidden_area": forbidden_area,
        "allowed_area": allowed_area,
        "planting_count": planting_count,
        "density_per_1000m2": density_per_1000m2,
        "candidate_points": total_candidates,
        "accepted_points": planting_count,
        "rejected_points": len(rejected),
        "planting_types": type_counts,
        "planting_config": planting_config_report,
        "source_snapshot_before": (
            ctx.source_snapshot_before.to_dict()
            if ctx.source_snapshot_before is not None
            else {}
        ),
        "rules_applied": catalog.to_report(),
        "normative_documents": default_rules.get("normative_documents", []),
        "verification_required": default_rules.get("verification_required", []),
    }
