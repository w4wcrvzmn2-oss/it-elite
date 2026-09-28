"""Visualization API routes."""

from __future__ import annotations

import json
import threading
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.api.jobs import JobStatus, get_job_store
from app.visualization.service import generate_visualizations, list_visualizations

router = APIRouter(prefix="/api/visualizations", tags=["Visualizations"])

_viz_status: dict[str, dict] = {}


@router.post("/generate")
def start_visualization(body: dict) -> dict:
    job_id = body.get("job_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id required")

    store = get_job_store()
    job = store.get_job(job_id)
    if not job or job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Job not found")

    file_info = store.get_file(job.file_id)
    if not file_info or not job.result:
        raise HTTPException(status_code=400, detail="Job data unavailable")

    _viz_status[job_id] = {"status": "processing", "message": "Подготовка плана..."}

    def _run() -> None:
        try:
            _viz_status[job_id] = {"status": "processing", "message": "Генерация визуализаций..."}
            items = generate_visualizations(
                Path(file_info["path"]),
                job.output_dir,
                job.run_report,
                job.result.accepted_plantings,
                job.output_dir / "config.yaml",
            )
            _viz_status[job_id] = {"status": "completed", "visualizations": items}
        except Exception as e:
            _viz_status[job_id] = {"status": "error", "error": str(e)}

    threading.Thread(target=_run, daemon=True).start()
    return {"status": "processing"}


@router.get("/{job_id}")
def get_visualizations(job_id: str) -> dict:
    if job_id in _viz_status:
        return _viz_status[job_id]

    store = get_job_store()
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    items = list_visualizations(job.output_dir)
    return {"status": "completed" if items else "not_started", "visualizations": items}


@router.get("/{job_id}/{viz_id}/image")
def get_visualization_image(job_id: str, viz_id: str) -> FileResponse:
    store = get_job_store()
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    viz_dir = job.output_dir / "visualizations"
    for name in (f"{viz_id}.png", f"ai_{viz_id}.png", f"plan_{viz_id}.png"):
        path = viz_dir / name
        if path.exists():
            return FileResponse(path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Visualization not found")
