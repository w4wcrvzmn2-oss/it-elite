"""API request/response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    status: str = "uploaded"


class AnalyzeConfig(BaseModel):
    tree_spacing: float | None = None
    shrub_spacing: float | None = None
    communication_buffer: float | None = None
    tree_max_count: int | None = None
    shrub_max_count: int | None = None
    tree_target_density: float | None = None
    shrub_target_density: float | None = None


class AnalyzeRequest(BaseModel):
    file_id: str
    demo: bool = False
    config: AnalyzeConfig | None = None


class AnalyzeResponse(BaseModel):
    job_id: str
    status: str = "queued"


class MapAreaRequest(BaseModel):
    """WGS84 bounding box from map selection (south-west corner origin)."""

    south: float = Field(..., ge=-90, le=90, description="Min latitude")
    west: float = Field(..., ge=-180, le=180, description="Min longitude")
    north: float = Field(..., ge=-90, le=90, description="Max latitude")
    east: float = Field(..., ge=-180, le=180, description="Max longitude")
    label: str | None = Field(None, description="Optional place label")
    config: AnalyzeConfig | None = None


class MapAreaPreviewResponse(BaseModel):
    buildings: int
    roads: int
    width_m: float
    height_m: float
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int = 0
    stage: str = ""
    error: str | None = None
    filename: str | None = None


class SiteStatistics(BaseModel):
    site_area_m2: float = 0
    forbidden_area_m2: float = 0
    allowed_area_m2: float = 0
    planting_count: int = 0
    density_per_1000m2: float = 0
    tree_count: int = 0
    shrub_count: int = 0
    communications: int = 0
    processing_time_sec: float = 0
    planting_config: dict[str, Any] = Field(default_factory=dict)
    rules_applied: list[dict[str, Any]] = Field(default_factory=list)
    normative_verification_required: bool = False


class RuleCheckSchema(BaseModel):
    rule: str
    value: float | None = None
    required: float
    status: str
    regulation: str
    clause: str = "TODO_VERIFY"
    description: str = ""


class PlantingSchema(BaseModel):
    id: str
    type: str
    x: float
    y: float
    status: str
    score: float = 0
    checks: list[RuleCheckSchema] = Field(default_factory=list)
    distances: dict[str, float | None] = Field(default_factory=dict)
    explanation: str = ""


class InterpretationResponse(BaseModel):
    plantings: list[PlantingSchema] = Field(default_factory=list)
    rejected_count: int = 0
    rules_applied: list[dict[str, Any]] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


class GeometryFeature(BaseModel):
    type: str = "Feature"
    geometry: dict[str, Any]
    properties: dict[str, Any] = Field(default_factory=dict)


class GeometryResponse(BaseModel):
    bounds: list[float] = Field(default_factory=list)
    site: list[GeometryFeature] = Field(default_factory=list)
    communications: list[GeometryFeature] = Field(default_factory=list)
    buildings: list[GeometryFeature] = Field(default_factory=list)
    roads: list[GeometryFeature] = Field(default_factory=list)
    restricted_zones: list[GeometryFeature] = Field(default_factory=list)
    allowed_area: list[GeometryFeature] = Field(default_factory=list)
    trees: list[GeometryFeature] = Field(default_factory=list)
    shrubs: list[GeometryFeature] = Field(default_factory=list)
