"""Export package tests."""

from pathlib import Path

import pytest

from app.export.package import (
    generate_constraints_json,
    generate_planting_csv,
    generate_project_summary_md,
)


def test_planting_csv_from_interpretation(project_root: Path, test_dxf_path: Path, output_dir: Path):
    from app.pipeline import run_pipeline

    config = project_root / "config" / "default.yaml"
    result = run_pipeline(test_dxf_path, output_dir / "result.dxf", config)
    csv_text = generate_planting_csv(result.interpretation_json)
    assert "id,type,x,y" in csv_text.replace(" ", "")
    assert "tree" in csv_text or "shrub" in csv_text


def test_constraints_json():
    report = {
        "site_area_m2": 1000,
        "allowed_area_m2": 800,
        "forbidden_area_m2": 200,
        "planting_count": 10,
        "planting_types": {"tree": 5, "shrub": 5},
        "rules_applied": [{"clause": "TODO_VERIFY"}],
    }
    data = generate_constraints_json(report)
    assert data["verification_status"]["requires_expert_verification"] is True


def test_project_summary_md():
    md = generate_project_summary_md("test.dxf", {"site_area_m2": 100, "planting_count": 5, "planting_types": {}})
    assert "Green Planner" in md
    assert "test.dxf" in md


def test_pdf_report(tmp_path):
    from app.export.pdf_report import generate_pdf_report

    out = tmp_path / "report.pdf"
    generate_pdf_report(out, "test.dxf", {
        "site_area_m2": 1000,
        "allowed_area_m2": 800,
        "forbidden_area_m2": 200,
        "planting_count": 10,
        "planting_types": {"tree": 5, "shrub": 5},
        "rules_applied": [{"regulation": "743-ПП", "clause": "TODO_VERIFY", "rule": "communication_distance"}],
    })
    assert out.exists()
    assert out.stat().st_size > 500
