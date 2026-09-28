"""Scenario API routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.api.jobs import JobStatus, get_job_store
from app.scenarios.service import (
    compare_scenarios,
    get_scenarios_status,
    load_scenarios_from_disk,
    start_scenarios_async,
)

router = APIRouter(prefix="/api/scenarios", tags=["Scenarios"])


@router.post("/{job_id}/generate")
def generate_scenarios(job_id: str) -> dict:
    store = get_job_store()
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")

    file_info = store.get_file(job.file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="Source file not found")

    start_scenarios_async(
        job_id,
        Path(file_info["path"]),
        job.output_dir,
        store.project_root,
    )
    return {"status": "processing", "message": "Расчёт сценариев запущен"}


@router.get("/{job_id}")
def get_scenarios(job_id: str) -> dict:
    store = get_job_store()
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    status = get_scenarios_status(job_id)
    if status["status"] != "unknown":
        comparison = compare_scenarios(status.get("scenarios", []))
        return {**status, "comparison": comparison}

    scenarios = load_scenarios_from_disk(job.output_dir)
    return {
        "status": "completed" if scenarios else "not_started",
        "scenarios": scenarios,
        "comparison": compare_scenarios(scenarios),
    }


@router.get("/{job_id}/compare")
def get_comparison(job_id: str) -> dict:
    data = get_scenarios(job_id)
    return data.get("comparison", {"rows": [], "scenarios": []})
