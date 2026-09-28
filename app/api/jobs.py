"""In-memory job store for API processing."""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from app.api.geometry_export import export_geometry, plantings_to_schema
from app.config import load_config
from app.pipeline import PipelineContext, PipelineError, run_pipeline


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


STAGES = [
    ("import", "Импорт DXF", 10),
    ("geometry", "Анализ геометрии", 25),
    ("restrictions", "Построение ограничений", 40),
    ("optimization", "Генерация посадок", 60),
    ("validation", "Проверка посадок", 80),
    ("export", "Экспорт результата", 95),
    ("completed", "Расчёт завершён", 100),
]


@dataclass
class Job:
    job_id: str
    file_id: str
    filename: str
    status: JobStatus = JobStatus.QUEUED
    progress: int = 0
    stage: str = "Queued"
    error: str | None = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    output_dir: Path | None = None
    result: Any = None
    context: PipelineContext | None = None
    run_report: dict[str, Any] = field(default_factory=dict)
    layer_categories: dict[str, list[str]] = field(default_factory=dict)


class JobStore:
    """Thread-safe in-memory job store."""

    def __init__(self, base_dir: Path, project_root: Path) -> None:
        self.base_dir = base_dir
        self.project_root = project_root
        self.uploads_dir = base_dir / "uploads"
        self.jobs_dir = base_dir / "jobs"
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self._jobs: dict[str, Job] = {}
        self._files: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def save_upload(self, filename: str, content: bytes) -> str:
        file_id = str(uuid.uuid4())
        path = self.uploads_dir / f"{file_id}.dxf"
        path.write_bytes(content)
        with self._lock:
            self._files[file_id] = {
                "file_id": file_id,
                "filename": filename,
                "path": str(path),
                "size": len(content),
            }
        return file_id

    def get_file(self, file_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._files.get(file_id)

    def _ensure_fixture(self, filename: str, script_name: str, create_fn: str) -> Path:
        path = self.project_root / "data" / "input" / filename
        if not path.exists():
            import importlib.util

            script = self.project_root / "scripts" / script_name
            if script.exists():
                spec = importlib.util.spec_from_file_location(script_name.replace(".py", ""), script)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                getattr(mod, create_fn)(path)
        return path

    def register_demo_file(self) -> str:
        demo_path = self._ensure_fixture(
            "synthetic_complex.dxf", "create_complex_dxf.py", "create_complex_dxf"
        )
        content = demo_path.read_bytes()
        file_id = self.save_upload("synthetic_complex.dxf", content)
        return file_id

    def register_realistic_demo_file(self) -> str:
        demo_path = self._ensure_fixture(
            "urban_courtyard_block.dxf", "create_realistic_dxf.py", "create_realistic_dxf"
        )
        content = demo_path.read_bytes()
        file_id = self.save_upload("urban_courtyard_block.dxf", content)
        return file_id

    def create_job(self, file_id: str) -> Job:
        file_info = self.get_file(file_id)
        if not file_info:
            raise ValueError(f"File not found: {file_id}")
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            file_id=file_id,
            filename=file_info["filename"],
            output_dir=self.jobs_dir / job_id,
        )
        job.output_dir.mkdir(parents=True, exist_ok=True)
        with self._lock:
            self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update_job(self, job_id: str, **kwargs: Any) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                for k, v in kwargs.items():
                    setattr(job, k, v)

    def run_job(self, job_id: str, config_overrides: dict[str, Any] | None = None) -> None:
        job = self.get_job(job_id)
        if not job:
            return

        file_info = self.get_file(job.file_id)
        if not file_info:
            self.update_job(job_id, status=JobStatus.ERROR, error="File not found")
            return

        def _set_stage(stage_key: str) -> None:
            for key, label, pct in STAGES:
                if key == stage_key:
                    self.update_job(job_id, status=JobStatus.PROCESSING, stage=label, progress=pct)
                    break

        try:
            self.update_job(job_id, status=JobStatus.PROCESSING, stage="Importing DXF", progress=5)
            _set_stage("import")

            config_path = job.output_dir / "config.yaml"
            base_config_path = self.project_root / "config" / "default.yaml"
            with open(base_config_path) as f:
                cfg = yaml.safe_load(f)

            if config_overrides:
                if config_overrides.get("tree_spacing") is not None:
                    cfg["planting"]["tree"]["min_spacing"] = config_overrides["tree_spacing"]
                if config_overrides.get("shrub_spacing") is not None:
                    cfg["planting"]["shrub"]["min_spacing"] = config_overrides["shrub_spacing"]
                if config_overrides.get("communication_buffer") is not None:
                    cfg["rules"]["communication"]["default_buffer"] = config_overrides["communication_buffer"]
                if config_overrides.get("tree_max_count") is not None:
                    cfg["planting"]["tree"]["max_count"] = config_overrides["tree_max_count"]
                if config_overrides.get("shrub_max_count") is not None:
                    cfg["planting"]["shrub"]["max_count"] = config_overrides["shrub_max_count"]
                if config_overrides.get("tree_target_density") is not None:
                    cfg["planting"]["tree"]["target_density"] = config_overrides["tree_target_density"]
                if config_overrides.get("shrub_target_density") is not None:
                    cfg["planting"]["shrub"]["target_density"] = config_overrides["shrub_target_density"]

            with open(config_path, "w") as f:
                yaml.dump(cfg, f)

            _set_stage("geometry")
            input_path = Path(file_info["path"])
            output_path = job.output_dir / "result.dxf"

            _set_stage("restrictions")
            _set_stage("optimization")

            result = run_pipeline(input_path, output_path, config_path)

            _set_stage("validation")
            _set_stage("export")

            with open(result.run_report_json) as f:
                run_report = json.load(f)

            geometry = export_geometry(
                result.context,
                result.accepted_plantings,
                result.context.document,
                {},
            )

            plantings = plantings_to_schema(result.accepted_plantings)

            with open(job.output_dir / "geometry.json", "w") as f:
                json.dump(geometry.model_dump(), f)

            with open(job.output_dir / "plantings.json", "w") as f:
                json.dump([p.model_dump() for p in plantings], f)

            from app.export.package import write_job_exports as _write_exports

            _write_exports(job.output_dir, job.filename, run_report)

            self.update_job(
                job_id,
                status=JobStatus.COMPLETED,
                progress=100,
                stage="Расчёт завершён",
                result=result,
                context=result.context,
                run_report=run_report,
            )
        except PipelineError as e:
            self.update_job(job_id, status=JobStatus.ERROR, error=str(e), progress=0, stage="Error")
        except Exception as e:
            self.update_job(job_id, status=JobStatus.ERROR, error=str(e), progress=0, stage="Error")


_store: JobStore | None = None


def get_job_store() -> JobStore:
    global _store
    if _store is None:
        project_root = Path(__file__).resolve().parent.parent.parent
        base = project_root / "data" / "api"
        _store = JobStore(base, project_root)
    return _store
