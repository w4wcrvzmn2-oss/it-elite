"""Export pipeline geometry to GeoJSON-like format for frontend."""

from __future__ import annotations

from typing import Any

from shapely.geometry import mapping
from shapely.geometry.base import BaseGeometry

from app.api.schemas import GeometryFeature, GeometryResponse, PlantingSchema
from app.dxf.entities import DxfDocument
from app.pipeline import PipelineContext
from app.planting.models import PlantingPoint


def _geom_to_feature(
    geom: BaseGeometry,
    properties: dict[str, Any] | None = None,
) -> GeometryFeature | None:
    if geom is None or geom.is_empty:
        return None
    try:
        return GeometryFeature(
            geometry=mapping(geom),
            properties=properties or {},
        )
    except Exception:
        return None


def _geoms_to_features(
    geoms: list[BaseGeometry],
    base_props: dict[str, Any] | None = None,
) -> list[GeometryFeature]:
    features: list[GeometryFeature] = []
    for i, geom in enumerate(geoms):
        props = dict(base_props or {})
        props["index"] = i
        feat = _geom_to_feature(geom, props)
        if feat:
            features.append(feat)
    return features


def _planting_to_feature(p: PlantingPoint) -> GeometryFeature:
    return GeometryFeature(
        geometry={"type": "Point", "coordinates": [p.x, p.y]},
        properties={
            "id": p.id,
            "type": p.planting_type,
            "status": p.status,
            "score": p.score,
        },
    )


def export_geometry(
    ctx: PipelineContext,
    plantings: list[PlantingPoint],
    document: DxfDocument,
    layer_categories: dict[str, list[str]],
) -> GeometryResponse:
    """Build geometry response from pipeline context."""
    bounds: list[float] = []
    all_geoms: list[BaseGeometry] = []

    for obj in document.objects:
        if obj.geometry is not None:
            all_geoms.append(obj.geometry)

    if ctx.planting_boundary is not None:
        all_geoms.append(ctx.planting_boundary)
    if ctx.forbidden_zone is not None:
        all_geoms.append(ctx.forbidden_zone)
    if ctx.allowed_area is not None:
        all_geoms.append(ctx.allowed_area)

    if all_geoms:
        minx = min(g.bounds[0] for g in all_geoms)
        miny = min(g.bounds[1] for g in all_geoms)
        maxx = max(g.bounds[2] for g in all_geoms)
        maxy = max(g.bounds[3] for g in all_geoms)
        padding = max(maxx - minx, maxy - miny) * 0.05
        bounds = [minx - padding, miny - padding, maxx + padding, maxy + padding]

    site_features: list[GeometryFeature] = []
    if ctx.planting_boundary is not None:
        feat = _geom_to_feature(ctx.planting_boundary, {"layer": "SITE", "category": "boundary"})
        if feat:
            site_features.append(feat)

    restricted: list[GeometryFeature] = []
    if ctx.forbidden_zone is not None:
        feat = _geom_to_feature(ctx.forbidden_zone, {"category": "restricted"})
        if feat:
            restricted.append(feat)

    allowed: list[GeometryFeature] = []
    if ctx.allowed_area is not None:
        feat = _geom_to_feature(ctx.allowed_area, {"category": "allowed"})
        if feat:
            allowed.append(feat)

    comm_features = _geoms_to_features(
        ctx.restriction_geometries.get("communications", []),
        {"category": "communication"},
    )
    building_features = _geoms_to_features(
        ctx.restriction_geometries.get("buildings", []),
        {"category": "building"},
    )
    road_features = _geoms_to_features(
        ctx.restriction_geometries.get("roads", []),
        {"category": "road"},
    )

    trees = [_planting_to_feature(p) for p in plantings if p.planting_type == "tree"]
    shrubs = [_planting_to_feature(p) for p in plantings if p.planting_type == "shrub"]

    return GeometryResponse(
        bounds=bounds,
        site=site_features,
        communications=comm_features,
        buildings=building_features,
        roads=road_features,
        restricted_zones=restricted,
        allowed_area=allowed,
        trees=trees,
        shrubs=shrubs,
    )


def plantings_to_schema(plantings: list[PlantingPoint]) -> list[PlantingSchema]:
    """Convert planting points to API schema."""
    from app.api.schemas import RuleCheckSchema

    result: list[PlantingSchema] = []
    for p in plantings:
        distances: dict[str, float | None] = {}
        for c in p.checks:
            if c.rule.endswith("_distance") and c.status == "passed":
                distances[c.rule.replace("_distance", "")] = c.value
            elif c.rule == "minimum_spacing" and c.status == "passed":
                distances["nearest_planting"] = c.value

        result.append(
            PlantingSchema(
                id=p.id,
                type=p.planting_type,
                x=p.x,
                y=p.y,
                status=p.status,
                score=p.score,
                checks=[
                    RuleCheckSchema(
                        rule=c.rule,
                        value=c.value,
                        required=c.required,
                        status=c.status,
                        regulation=c.regulation,
                        clause=c.clause,
                        description=c.description,
                    )
                    for c in p.checks
                ],
                distances=distances,
                explanation=p.explanation,
            )
        )
    return result
