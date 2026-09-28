"""API endpoint tests."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


@pytest.fixture
def test_dxf_bytes() -> bytes:
    path = Path(__file__).resolve().parent.parent / "data" / "input" / "test.dxf"
    if not path.exists():
        pytest.skip("test.dxf not found")
    return path.read_bytes()


def test_health() -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_upload_and_analyze(test_dxf_bytes: bytes) -> None:
    r = client.post(
        "/api/upload",
        files={"file": ("test.dxf", test_dxf_bytes, "application/dxf")},
    )
    assert r.status_code == 200
    file_id = r.json()["file_id"]

    r = client.post("/api/analyze", json={"file_id": file_id})
    assert r.status_code == 200
    job_id = r.json()["job_id"]

    for _ in range(60):
        r = client.get(f"/api/jobs/{job_id}")
        assert r.status_code == 200
        data = r.json()
        if data["status"] == "completed":
            break
        if data["status"] == "error":
            pytest.fail(f"Job failed: {data.get('error')}")
        time.sleep(0.5)
    else:
        pytest.fail("Job did not complete in time")

    r = client.get(f"/api/jobs/{job_id}/statistics")
    assert r.status_code == 200
    stats = r.json()
    assert stats["planting_count"] > 0

    r = client.get(f"/api/jobs/{job_id}/geometry")
    assert r.status_code == 200
    geom = r.json()
    assert len(geom["trees"]) > 0

    r = client.get(f"/api/jobs/{job_id}/interpretation")
    assert r.status_code == 200
    assert len(r.json()["plantings"]) > 0


def test_demo_upload() -> None:
    r = client.post("/api/demo/upload")
    assert r.status_code == 200
    assert "synthetic_complex" in r.json()["filename"]
