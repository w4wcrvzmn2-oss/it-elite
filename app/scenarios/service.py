"""Run deterministic scenarios and compare results."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

import yaml

from app.pipeline import run_pipeline
from app.scenarios.presets import SCENARIO_PRESETS

_scenario_jobs: dict[str, dict[str, Any]] = {}
_scenario_lock = threading.Lock()


def _stats_from_report(report: dict, processing_time: float) -> dict:
    types = report.get("planting_types", {})
    return {
        "tree_count": types.get("tree", 0),
        "shrub_count": types.get("shrub", 0),
        "planting_count": report.get("planting_count", 0),
        "allowed_area_m2": report.get("allowed_area_m2", 0),
        "forbidden_area_m2": report.get("forbidden_area_m2", 0),
        "density_per_1000m2": report.get("density_per_1000m2", 0),
        "rejected_points": report.get("rejected_points", 0),
        "processing_time_sec": processing_time,
    }


def run_scenarios_for_job(
    job_id: str,
    input_path: Path,
    output_dir: Path,
    project_root: Path,
    on_progress: Any = None,
) -> list[dict]:
    scenarios_dir = output_dir / "scenarios"
    scenarios_dir.mkdir(parents=True, exist_ok=True)
    base_config = project_root / "config" / "default.yaml"
    results: list[dict] = []

    for preset_id, preset in SCENARIO_PRESETS.items():
        if on_progress:
            on_progress(preset_id, "processing")
        scenario_dir = scenarios_dir / preset_id
        scenario_dir.mkdir(parents=True, exist_ok=True)
        config_path = scenario_dir / "config.yaml"

        with open(base_config) as f:
            cfg = yaml.safe_load(f)
        for key, val in preset["overrides"].items():
            if key == "tree_spacing":
                cfg["planting"]["tree"]["min_spacing"] = val
            elif key == "shrub_spacing":
                cfg["planting"]["shrub"]["min_spacing"] = val
            elif key == "tree_max_count":
                cfg["planting"]["tree"]["max_count"] = val
            elif key == "shrub_max_count":
                cfg["planting"]["shrub"]["max_count"] = val
            elif key == "tree_target_density":
                cfg["planting"]["tree"]["target_density"] = val
            elif key == "shrub_target_density":
                cfg["planting"]["shrub"]["target_density"] = val

        with open(config_path, "w") as f:
            yaml.dump(cfg, f)

        result = run_pipeline(input_path, scenario_dir / "result.dxf", config_path)
        with open(result.run_report_json) as f:
            report = json.load(f)

        stats = _stats_from_report(report, result.processing_time_sec)
        entry = {
            "id": preset_id,
            "name": preset["name"],
            "description": preset["description"],
            "status": "completed",
            **stats,
        }
        with open(scenario_dir / "scenario.json", "w") as f:
            json.dump(entry, f, ensure_ascii=False, indent=2)
        results.append(entry)
        if on_progress:
            on_progress(preset_id, "completed")

    with open(scenarios_dir / "comparison.json", "w") as f:
        json.dump({"scenarios": results}, f, ensure_ascii=False, indent=2)
    return results


def start_scenarios_async(job_id: str, input_path: Path, output_dir: Path, project_root: Path) -> None:
    with _scenario_lock:
        _scenario_jobs[job_id] = {"status": "processing", "scenarios": [], "error": None}

    def _run() -> None:
        try:
            results = run_scenarios_for_job(job_id, input_path, output_dir, project_root)
            with _scenario_lock:
                _scenario_jobs[job_id] = {"status": "completed", "scenarios": results, "error": None}
        except Exception as e:
            with _scenario_lock:
                _scenario_jobs[job_id] = {"status": "error", "scenarios": [], "error": str(e)}

    threading.Thread(target=_run, daemon=True).start()


def get_scenarios_status(job_id: str) -> dict:
    with _scenario_lock:
        if job_id in _scenario_jobs:
            return _scenario_jobs[job_id]
    return {"status": "unknown", "scenarios": [], "error": None}


def load_scenarios_from_disk(output_dir: Path) -> list[dict]:
    comp = output_dir / "scenarios" / "comparison.json"
    if comp.exists():
        with open(comp) as f:
            return json.load(f).get("scenarios", [])
    scenarios_dir = output_dir / "scenarios"
    if not scenarios_dir.exists():
        return []
    results = []
    for sub in scenarios_dir.iterdir():
        meta = sub / "scenario.json"
        if meta.exists():
            with open(meta) as f:
                results.append(json.load(f))
    return results


def compare_scenarios(scenarios: list[dict]) -> dict:
    if not scenarios:
        return {"rows": [], "scenarios": []}
    metrics = [
        ("tree_count", "Деревья"),
        ("shrub_count", "Кустарники"),
        ("planting_count", "Всего посадок"),
        ("allowed_area_m2", "Разрешённая площадь, м²"),
        ("density_per_1000m2", "Плотность / 1000 м²"),
        ("rejected_points", "Отклонённых кандидатов"),
        ("processing_time_sec", "Время расчёта, с"),
    ]
    rows = []
    for key, label in metrics:
        rows.append({"metric": label, "key": key, "values": {s["id"]: s.get(key) for s in scenarios}})
    return {
        "scenarios": [{"id": s["id"], "name": s["name"], "description": s.get("description", "")} for s in scenarios],
        "rows": rows,
    }
