#!/usr/bin/env python3
"""One-shot API E2E QA for Green Planner demo. Does not print secrets."""

from __future__ import annotations

import base64
import io
import json
import os
import sys
import time
import zipfile
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
BASE = os.getenv("E2E_API_BASE", "http://127.0.0.1:8000")
INPUT_DXF = ROOT / "data/input/urban_courtyard_block.dxf"
FALLBACK_DXF = ROOT / "data/input/synthetic_complex.dxf"
OUT = ROOT / "data/output/e2e_qa_report.json"

# load .env without printing
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def section(name: str) -> None:
    print(f"\n=== {name} ===")


def ok(msg: str) -> None:
    print(f"  PASS: {msg}")


def partial(msg: str) -> None:
    print(f"  PARTIAL: {msg}")


def blocked(msg: str) -> None:
    print(f"  BLOCKED: {msg}")


def fail(msg: str) -> None:
    print(f"  FAIL: {msg}")


def dxf_layers(path: Path) -> dict[str, int]:
    import ezdxf

    doc = ezdxf.readfile(str(path))
    counts: dict[str, int] = {}
    msp = doc.modelspace()
    for e in msp:
        layer = e.dxf.layer
        counts[layer] = counts.get(layer, 0) + 1
    return counts


def poll_job(client: httpx.Client, job_id: str, timeout: float = 300) -> dict:
    start = time.time()
    while time.time() - start < timeout:
        r = client.get(f"{BASE}/api/jobs/{job_id}")
        r.raise_for_status()
        data = r.json()
        if data["status"] == "completed":
            return data
        if data["status"] == "error":
            raise RuntimeError(data.get("error") or "job error")
        time.sleep(1)
    raise TimeoutError("job timeout")


def poll_viz(client: httpx.Client, job_id: str, timeout: float = 180) -> dict:
    start = time.time()
    while time.time() - start < timeout:
        r = client.get(f"{BASE}/api/visualizations/{job_id}")
        r.raise_for_status()
        data = r.json()
        if data.get("status") in ("completed", "error"):
            return data
        time.sleep(2)
    raise TimeoutError("viz timeout")


def poll_scenarios(client: httpx.Client, job_id: str, timeout: float = 300) -> dict:
    start = time.time()
    while time.time() - start < timeout:
        r = client.get(f"{BASE}/api/scenarios/{job_id}")
        r.raise_for_status()
        data = r.json()
        if data.get("status") == "completed" and data.get("scenarios"):
            return data
        if data.get("status") == "error":
            raise RuntimeError(str(data))
        time.sleep(2)
    raise TimeoutError("scenarios timeout")


def main() -> int:
    report: dict = {"sections": {}, "job_id": None}
    client = httpx.Client(timeout=120)

    section("API health")
    r = client.get(f"{BASE}/api/health")
    docs = client.get(f"{BASE}/docs")
    report["sections"]["health"] = {
        "health_status": r.status_code,
        "docs_status": docs.status_code,
    }
    if r.status_code == 200 and docs.status_code == 200:
        ok(f"health={r.json()}, docs=200")
    else:
        fail(f"health={r.status_code}, docs={docs.status_code}")
        return 1

    section("Upload + analyze")
    dxf = INPUT_DXF if INPUT_DXF.exists() else FALLBACK_DXF
    with dxf.open("rb") as f:
        up = client.post(
            f"{BASE}/api/upload",
            files={"file": (dxf.name, f, "application/dxf")},
        )
    up.raise_for_status()
    file_id = up.json()["file_id"]
    ar = client.post(f"{BASE}/api/analyze", json={"file_id": file_id})
    ar.raise_for_status()
    job_id = ar.json()["job_id"]
    report["job_id"] = job_id
    ok(f"uploaded {dxf.name}, job_id={job_id}")

    t0 = time.time()
    poll_job(client, job_id)
    elapsed = time.time() - t0
    stats = client.get(f"{BASE}/api/jobs/{job_id}/statistics").json()
    report["sections"]["pipeline"] = {"elapsed_sec": round(elapsed, 2), "stats": stats}
    ok(f"analysis completed in {elapsed:.1f}s, plantings={stats['planting_count']}")

    store_dir = ROOT / "data/api/jobs" / job_id
    artifacts = [
        "result.dxf",
        "run_report.json",
        "interpretation.json",
        "geometry.json",
    ]
    missing = [a for a in artifacts if not (store_dir / a).exists()]
    if missing:
        fail(f"missing artifacts: {missing}")
    else:
        ok("core artifacts on disk")

    section("Export pipeline")
    write_exports = client.get(f"{BASE}/api/export/{job_id}/csv")
    write_exports.raise_for_status()
    for kind in ("summary", "constraints", "pdf", "zip"):
        er = client.get(f"{BASE}/api/export/{job_id}/{kind}")
        report.setdefault("sections", {}).setdefault("export", {})[kind] = {
            "status": er.status_code,
            "size": len(er.content),
            "content_type": er.headers.get("content-type"),
        }
        if er.status_code != 200:
            fail(f"export/{kind} -> {er.status_code}")
        else:
            ok(f"export/{kind} -> 200, {len(er.content)} bytes")

    pdf_bytes = client.get(f"{BASE}/api/export/{job_id}/pdf").content
    if pdf_bytes[:4] == b"%PDF" and len(pdf_bytes) > 500:
        ok("PDF header valid")
    else:
        fail("PDF invalid")

    zip_bytes = client.get(f"{BASE}/api/export/{job_id}/zip").content
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        expected = [
            "01_result/result.dxf",
            "02_analysis/run_report.json",
            "02_analysis/constraints.json",
            "02_analysis/interpretation.json",
            "03_planting/planting.csv",
            "05_report/project_summary.md",
            "README.txt",
        ]
        zip_missing = [e for e in expected if e not in names]
        has_pdf = "05_report/project_report.pdf" in names
        has_viz = any(n.startswith("06_visualizations/") for n in names)
        report["sections"]["zip"] = {
            "files": names,
            "missing": zip_missing,
            "has_pdf": has_pdf,
            "has_viz": has_viz,
        }
        if zip_missing:
            fail(f"ZIP missing: {zip_missing}")
        else:
            ok(f"ZIP structure OK ({len(names)} files)")
        if has_pdf:
            ok("ZIP contains project_report.pdf")
        else:
            partial("ZIP without PDF")

    section("DXF layers")
    input_layers = dxf_layers(dxf)
    output_layers = dxf_layers(store_dir / "result.dxf")
    source_layers = {"BUILDINGS", "ROADS", "WATER", "GAS", "PIPE", "BOUNDARY"}
    present_source = {l for l in source_layers if l in output_layers}
    planting_layers = {"PLANTING_TREES", "PLANTING_SHRUBS", "PLANTING_PROPOSED"}
    planting_ok = planting_layers.issubset(set(output_layers))
    overwritten = []
    for layer in present_source:
        if input_layers.get(layer, 0) != output_layers.get(layer, 0):
            overwritten.append(
                f"{layer}: in={input_layers.get(layer)} out={output_layers.get(layer)}"
            )
    report["sections"]["layers"] = {
        "input_layers": input_layers,
        "output_layers": output_layers,
        "planting_layers_ok": planting_ok,
        "source_preserved": not overwritten,
        "overwritten": overwritten,
    }
    if planting_ok:
        ok("PLANTING_TREES/SHRUBS/PROPOSED present")
    else:
        fail(f"missing planting layers: {planting_layers - set(output_layers)}")
    if not overwritten:
        ok("source layer entity counts preserved")
    else:
        partial(f"layer count diffs: {overwritten[:3]}")

    section("Why Here")
    interp = client.get(f"{BASE}/api/jobs/{job_id}/interpretation").json()
    planting = interp["plantings"][0]
    why_here = {
        "id": planting["id"],
        "type": planting["type"],
        "x": planting["x"],
        "y": planting["y"],
        "distances": planting.get("distances"),
        "checks": planting.get("checks"),
        "explanation": planting.get("explanation"),
    }
    report["sections"]["why_here"] = why_here
    if planting.get("explanation") and planting.get("checks"):
        ok(f"planting {planting['id']} has deterministic explanation + {len(planting['checks'])} checks")
    else:
        fail("why here data incomplete")

    section("Why Not Here")
    rej_x, rej_y = 0.0, 0.0
    if interp.get("rejected_count", 0) > 0:
        # use run_report rejected sample via interpretation file
        interp_path = store_dir / "interpretation.json"
        data = json.loads(interp_path.read_text())
        rejected = data.get("rejected") or []
        if rejected:
            rej_x, rej_y = rejected[0]["x"], rejected[0]["y"]
    else:
        rej_x, rej_y = planting["x"] + 50, planting["y"] + 50
    wn = client.post(
        f"{BASE}/api/ai/why-not",
        json={"job_id": job_id, "x": rej_x, "y": rej_y},
    )
    wn.raise_for_status()
    wn_data = wn.json()
    report["sections"]["why_not"] = wn_data
    if wn_data.get("reasons"):
        ok(f"why-not returned {len(wn_data['reasons'])} reasons")
    else:
        fail("why-not empty")

    section("OpenRouter text")
    ai_status = client.get(f"{BASE}/api/ai/status").json()
    has_key = bool(os.getenv("OPENROUTER_API_KEY", "").strip())
    report["sections"]["ai"] = {"status": ai_status, "key_present": has_key}
    t1 = time.time()
    ex = client.post(
        f"{BASE}/api/ai/explain-planting",
        json={"job_id": job_id, "planting_id": planting["id"]},
    )
    lat1 = time.time() - t1
    ex.raise_for_status()
    ex1 = ex.json()
    t2 = time.time()
    ex2 = client.post(
        f"{BASE}/api/ai/explain-planting",
        json={"job_id": job_id, "planting_id": planting["id"]},
    ).json()
    lat2 = time.time() - t2
    report["sections"]["ai"]["explain"] = {
        "latency1": round(lat1, 2),
        "latency2": round(lat2, 2),
        "fallback": ex1.get("fallback"),
        "ai_generated": ex1.get("ai_generated"),
        "has_summary": bool(ex1.get("summary")),
    }
    clauses = json.dumps(ex1)
    if "TODO_VERIFY" in clauses or ex1.get("fallback"):
        ok("normative clauses not invented (TODO_VERIFY or fallback)")
    else:
        partial("check normative clauses manually")
    if has_key and ex1.get("ai_generated"):
        ok(f"live AI explain-planting {lat1:.1f}s, cache second={lat2:.1f}s")
    elif ex1.get("fallback"):
        ok(f"fallback explain-planting works ({lat1:.1f}s)")
    else:
        partial("unexpected AI state")

    section("Scenarios")
    client.post(f"{BASE}/api/scenarios/{job_id}/generate")
    sc = poll_scenarios(client, job_id)
    ids = {s["id"] for s in sc["scenarios"]}
    report["sections"]["scenarios"] = {
        "ids": sorted(ids),
        "count": len(sc["scenarios"]),
        "comparison_rows": len(sc.get("comparison", {}).get("rows", [])),
    }
    for sid in ("dense", "balanced", "minimal"):
        if sid not in ids:
            fail(f"missing scenario {sid}")
        else:
            s = next(x for x in sc["scenarios"] if x["id"] == sid)
            ok(f"{sid}: trees={s['tree_count']} shrubs={s['shrub_count']} total={s['planting_count']}")

    section("AI scenario comparison")
    cmp = client.post(f"{BASE}/api/ai/compare-scenarios", json={"job_id": job_id}).json()
    report["sections"]["ai_compare"] = {
        "fallback": cmp.get("fallback"),
        "differences_count": len(cmp.get("differences") or []),
        "summary_len": len(cmp.get("summary") or ""),
    }
    if cmp.get("summary"):
        ok("AI compare returned summary")
    else:
        partial("AI compare empty summary")

    section("Plan visualizations")
    client.post(f"{BASE}/api/visualizations/generate", json={"job_id": job_id})
    viz = poll_viz(client, job_id)
    items = viz.get("visualizations") or []
    plan_items = [v for v in items if v.get("kind") == "plan" or str(v.get("id", "")).startswith("plan_")]
    ai_items = [v for v in items if v.get("ai_generated") or v.get("kind") == "ai"]
    report["sections"]["viz"] = {
        "total": len(items),
        "plan": len(plan_items),
        "ai": len(ai_items),
        "items": [{k: v[k] for k in ("id", "kind", "ai_generated", "badge") if k in v} for v in items],
    }
    if plan_items:
        ok(f"{len(plan_items)} engineer plan images")
        img = client.get(f"{BASE}/api/visualizations/{job_id}/{plan_items[0]['id']}/image")
        if img.status_code == 200 and img.headers.get("content-type", "").startswith("image"):
            ok("plan image served")
        else:
            fail("plan image fetch failed")
    else:
        fail("no plan images")

    section("AI image E2E")
    image_model = os.getenv("OPENROUTER_IMAGE_MODEL", "").strip()
    if not image_model:
        blocked("OPENROUTER_IMAGE_MODEL not set — set e.g. bytedance-seed/seedream-4.5")
        # probe unified images API once if key present
        if has_key:
            probe_model = "bytedance-seed/seedream-4.5"
            pr = httpx.post(
                f"{os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')}/images",
                headers={
                    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": probe_model,
                    "prompt": "Test urban courtyard green planting overview, 16:9",
                    "aspect_ratio": "16:9",
                    "n": 1,
                },
                timeout=120,
            )
            report["sections"]["ai_image_probe"] = {
                "model": probe_model,
                "status": pr.status_code,
                "ok": pr.status_code == 200,
            }
            if pr.status_code == 200:
                partial(f"provider probe via /images OK (model={probe_model}), but OPENROUTER_IMAGE_MODEL unset in env")
            else:
                partial(f"provider probe failed HTTP {pr.status_code} (adapter may need /images endpoint)")
    else:
        # single image via direct function to avoid generating all 3
        os.environ["OPENROUTER_IMAGE_MODEL"] = image_model
        from app.visualization.image_gen import generate_ai_image

        ib, model_used = generate_ai_image("Test single image urban green courtyard")
        report["sections"]["ai_image"] = {
            "model": model_used,
            "bytes": len(ib) if ib else 0,
        }
        if ib and len(ib) > 1000:
            ok(f"single AI image {len(ib)} bytes via {model_used}")
        else:
            partial("AI image generation returned empty — check adapter/chat vs /images API")

    section("Normatives in stats")
    if stats.get("normative_verification_required") and stats.get("rules_applied"):
        ok(f"rules_applied={len(stats['rules_applied'])}, verification required")
    else:
        partial("normative flags unexpected")

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nReport saved: {OUT}")
    print(f"DEMO JOB ID: {job_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
