"""FastAPI application entry point."""

from __future__ import annotations

import json
import threading
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app import __version__
from app.api.geometry_export import export_geometry, plantings_to_schema
from app.api.jobs import JobStatus, get_job_store
from app.api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    GeometryResponse,
    HealthResponse,
    InterpretationResponse,
    JobStatusResponse,
    MapAreaPreviewResponse,
    MapAreaRequest,
    PlantingSchema,
    RuleCheckSchema,
    SiteStatistics,
    UploadResponse,
)
from app.osm import bbox_size_meters, fetch_osm_features, generate_dxf_from_osm
from app.api.routes.ai import router as ai_router
from app.api.routes.export import router as export_router
from app.api.routes.scenarios import router as scenarios_router
from app.api.routes.visualizations import router as visualizations_router
from app.api.server import _load_dotenv
from app.export.package import write_job_exports
from app.interpretation.generator import load_interpretation

_load_dotenv()

app = FastAPI(
    title="Green Planner API",
    description="Automated urban planting planning API",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router)
app.include_router(export_router)
app.include_router(scenarios_router)
app.include_router(visualizations_router)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(version=__version__)


@app.post("/api/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename or not file.filename.lower().endswith(".dxf"):
        raise HTTPException(status_code=400, detail="Only DXF files are supported")
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    store = get_job_store()
    file_id = store.save_upload(file.filename, content)
    return UploadResponse(
        file_id=file_id,
        filename=file.filename,
        size=len(content),
    )


@app.post("/api/demo/upload", response_model=UploadResponse)
def demo_upload() -> UploadResponse:
    store = get_job_store()
    file_id = store.register_demo_file()
    info = store.get_file(file_id)
    assert info is not None
    return UploadResponse(
        file_id=file_id,
        filename=info["filename"],
        size=info["size"],
    )


@app.post("/api/demo/upload-realistic", response_model=UploadResponse)
def demo_upload_realistic() -> UploadResponse:
    store = get_job_store()
    file_id = store.register_realistic_demo_file()
    info = store.get_file(file_id)
    assert info is not None
    return UploadResponse(
        file_id=file_id,
        filename=info["filename"],
        size=info["size"],
    )


MAX_MAP_SIDE_M = 450.0
MIN_MAP_SIDE_M = 40.0


def _validate_map_bbox(req: MapAreaRequest) -> tuple[float, float]:
    if req.north <= req.south or req.east <= req.west:
        raise HTTPException(status_code=400, detail="Некорректный bounding box")
    width_m, height_m = bbox_size_meters(req.south, req.west, req.north, req.east)
    if width_m < MIN_MAP_SIDE_M or height_m < MIN_MAP_SIDE_M:
        raise HTTPException(
            status_code=400,
            detail=f"Участок слишком маленький (мин. {MIN_MAP_SIDE_M:.0f} м)",
        )
    if width_m > MAX_MAP_SIDE_M or height_m > MAX_MAP_SIDE_M:
        raise HTTPException(
            status_code=400,
            detail=f"Участок слишком большой (макс. {MAX_MAP_SIDE_M:.0f} м)",
        )
    return width_m, height_m


@app.post("/api/map/preview", response_model=MapAreaPreviewResponse)
def preview_map_area(request: MapAreaRequest) -> MapAreaPreviewResponse:
    """Preview OSM data availability for selected map area."""
    width_m, height_m = _validate_map_bbox(request)
    try:
        osm = fetch_osm_features(request.south, request.west, request.north, request.east)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"OpenStreetMap перегружен, выберите участок ещё раз. {e}",
        ) from e
    b_count = len(osm.get("buildings", []))
    r_count = len(osm.get("roads", []))
    if b_count == 0 and r_count == 0:
        msg = "В выбранной области не найдено зданий и дорог OSM"
    else:
        msg = "Данные OpenStreetMap получены"
    return MapAreaPreviewResponse(
        buildings=b_count,
        roads=r_count,
        width_m=round(width_m, 1),
        height_m=round(height_m, 1),
        message=msg,
    )


@app.post("/api/analyze/from-map", response_model=AnalyzeResponse)
def analyze_from_map(request: MapAreaRequest) -> AnalyzeResponse:
    """Fetch OSM for bbox, build synthetic DXF, run deterministic pipeline."""
    width_m, height_m = _validate_map_bbox(request)
    try:
        osm = fetch_osm_features(request.south, request.west, request.north, request.east)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"OpenStreetMap перегружен, выберите участок ещё раз. {e}",
        ) from e

    if not osm.get("buildings") and not osm.get("roads"):
        raise HTTPException(
            status_code=400,
            detail="В выбранной области нет данных OSM для расчёта",
        )

    dxf_bytes = generate_dxf_from_osm(
        request.south, request.west, request.north, request.east, osm
    )
    label = request.label or "moscow_map"
    filename = f"{label}_{int(width_m)}x{int(height_m)}m.dxf"

    store = get_job_store()
    file_id = store.save_upload(filename, dxf_bytes)
    job = store.create_job(file_id)
    overrides = request.config.model_dump(exclude_none=True) if request.config else None

    thread = threading.Thread(target=store.run_job, args=(job.job_id, overrides), daemon=True)
    thread.start()

    return AnalyzeResponse(job_id=job.job_id, status="queued")


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    store = get_job_store()
    file_id = request.file_id
    if request.demo:
        file_id = store.register_demo_file()

    if not store.get_file(file_id):
        raise HTTPException(status_code=404, detail="File not found")

    job = store.create_job(file_id)
    overrides = request.config.model_dump(exclude_none=True) if request.config else None

    thread = threading.Thread(target=store.run_job, args=(job.job_id, overrides), daemon=True)
    thread.start()

    return AnalyzeResponse(job_id=job.job_id, status="queued")


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str) -> JobStatusResponse:
    store = get_job_store()
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status.value,
        progress=job.progress,
        stage=job.stage,
        error=job.error,
        filename=job.filename,
    )


@app.get("/api/jobs/{job_id}/statistics", response_model=SiteStatistics)
def get_statistics(job_id: str) -> SiteStatistics:
    store = get_job_store()
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")

    r = job.run_report
    types = r.get("planting_types", {})
    rules = r.get("rules_applied", [])
    todo = any(
        (rule.get("clause") or rule.get("regulation_clause")) == "TODO_VERIFY"
        for rule in rules
    )
    return SiteStatistics(
        site_area_m2=r.get("site_area_m2", 0),
        forbidden_area_m2=r.get("forbidden_area_m2", 0),
        allowed_area_m2=r.get("allowed_area_m2", 0),
        planting_count=r.get("planting_count", 0),
        density_per_1000m2=r.get("density_per_1000m2", 0),
        tree_count=types.get("tree", 0),
        shrub_count=types.get("shrub", 0),
        communications=r.get("communications", 0),
        processing_time_sec=r.get("processing_time_sec", 0),
        planting_config=r.get("planting_config", {}),
        rules_applied=rules,
        normative_verification_required=todo,
    )


@app.get("/api/jobs/{job_id}/interpretation", response_model=InterpretationResponse)
def get_interpretation(job_id: str) -> InterpretationResponse:
    store = get_job_store()
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")

    interp_path = job.output_dir / "interpretation.json"
    if interp_path.exists():
        report = load_interpretation(interp_path)
        return InterpretationResponse(
            plantings=[
                PlantingSchema(
                    id=p.id,
                    type=p.type,
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
                    distances=p.distances,
                    explanation=p.explanation,
                )
                for p in report.plantings
            ],
            rejected_count=report.summary.get("rejected_count", 0),
            rules_applied=report.rules_applied,
            summary=report.summary,
        )

    if job.result:
        plantings = plantings_to_schema(job.result.accepted_plantings)
        return InterpretationResponse(plantings=plantings)

    raise HTTPException(status_code=404, detail="Interpretation not found")


@app.get("/api/jobs/{job_id}/geometry", response_model=GeometryResponse)
def get_geometry(job_id: str) -> GeometryResponse:
    store = get_job_store()
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")

    geom_path = job.output_dir / "geometry.json"
    if geom_path.exists():
        with open(geom_path) as f:
            return GeometryResponse.model_validate(json.load(f))

    if job.result and job.context and job.context.document:
        geometry = export_geometry(
            job.context,
            job.result.accepted_plantings,
            job.context.document,
            {},
        )
        return geometry

    raise HTTPException(status_code=404, detail="Geometry not found")


@app.get("/api/jobs/{job_id}/result")
def get_result(job_id: str) -> JSONResponse:
    store = get_job_store()
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")
    return JSONResponse(content=job.run_report)


@app.get("/api/jobs/{job_id}/download/dxf")
def download_dxf(job_id: str) -> FileResponse:
    store = get_job_store()
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")
    path = job.output_dir / "result.dxf"
    if not path.exists():
        raise HTTPException(status_code=404, detail="DXF not found")
    return FileResponse(path, filename=f"planting_{job.filename}", media_type="application/dxf")


@app.get("/api/jobs/{job_id}/download/interpretation")
def download_interpretation(job_id: str) -> FileResponse:
    store = get_job_store()
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    path = job.output_dir / "interpretation.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Interpretation not found")
    return FileResponse(path, filename="interpretation.json", media_type="application/json")


@app.get("/api/jobs/{job_id}/download/report")
def download_report(job_id: str) -> FileResponse:
    store = get_job_store()
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    path = job.output_dir / "run_report.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(path, filename="run_report.json", media_type="application/json")
