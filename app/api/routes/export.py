"""Export API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response

from app.api.jobs import JobStatus, get_job_store
from app.export.package import build_export_package, write_job_exports

router = APIRouter(prefix="/api/export", tags=["Export"])


@router.get("/{job_id}/csv")
def download_csv(job_id: str) -> FileResponse:
    store = get_job_store()
    job = store.get_job(job_id)
    if not job or job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Job not found")
    write_job_exports(job.output_dir, job.filename, job.run_report)
    path = job.output_dir / "planting.csv"
    return FileResponse(path, filename="planting.csv", media_type="text/csv")


@router.get("/{job_id}/constraints")
def download_constraints(job_id: str) -> FileResponse:
    store = get_job_store()
    job = store.get_job(job_id)
    if not job or job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Job not found")
    write_job_exports(job.output_dir, job.filename, job.run_report)
    path = job.output_dir / "constraints.json"
    return FileResponse(path, filename="constraints.json", media_type="application/json")


@router.get("/{job_id}/summary")
def download_summary(job_id: str) -> FileResponse:
    store = get_job_store()
    job = store.get_job(job_id)
    if not job or job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Job not found")
    write_job_exports(job.output_dir, job.filename, job.run_report)
    path = job.output_dir / "project_summary.md"
    return FileResponse(path, filename="project_summary.md", media_type="text/markdown")


@router.get("/{job_id}/pdf")
def download_pdf(job_id: str) -> FileResponse:
    store = get_job_store()
    job = store.get_job(job_id)
    if not job or job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Job not found")
    write_job_exports(job.output_dir, job.filename, job.run_report)
    path = job.output_dir / "project_report.pdf"
    if not path.exists():
        raise HTTPException(status_code=404, detail="PDF not generated")
    return FileResponse(path, filename="project_report.pdf", media_type="application/pdf")


@router.get("/{job_id}/zip")
def download_zip(job_id: str) -> Response:
    store = get_job_store()
    job = store.get_job(job_id)
    if not job or job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Job not found")
    data = build_export_package(job.output_dir, job.filename, job.run_report)
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="green-planner-project.zip"'},
    )
