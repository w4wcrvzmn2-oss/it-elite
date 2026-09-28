# Demo Script (4–10 minutes)

## Prerequisites

```bash
cd /path/to/IT-Elite
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -e .
python scripts/create_test_dxf.py
python scripts/create_complex_dxf.py
```

> **Note:** Repository contains only synthetic DXF files.
> For final demonstration with organizer-provided data, place real DXF
> into `data/input/` and update layer mapping in `config/default.yaml`.

---

## Step 1: Show Input DXF (30 sec)

Open `data/input/synthetic_complex.dxf` (or `test.dxf`).

Explain contents:
- **SITE** — boundary 200×150 m
- **PIPE, WATER, GAS** — communications with crossing buffers
- **BUILDINGS** — 2 obstacles
- **ROADS** — top and bottom edges

---

## Step 2: Inspect Layers (1 min)

```bash
green-planner inspect --input data/input/synthetic_complex.dxf
```

Show:
- Layer list with entity counts
- Entity types (LINE, LWPOLYLINE)
- Bounding box and extent
- Units: `meters (INSUNITS=6)`

---

## Step 3: Run Processing (1 min)

```bash
green-planner process \
  --input data/input/synthetic_complex.dxf \
  --output data/output/demo_result.dxf \
  --config config/default.yaml
```

Show log:
- Communications detected: 3
- Allowed area vs forbidden area
- Accepted / rejected counts

---

## Step 4: Show Statistics (1 min)

```bash
cat data/output/run_report.json | python -m json.tool | head -30
```

Highlight:
- `site_area_m2`, `forbidden_area_m2`, `allowed_area_m2`
- `planting_count`, `density_per_1000m2`
- `planting_config.tree.min_spacing`
- `verification_required` list

---

## Step 5: Debug Visualization (1 min)

```bash
green-planner debug \
  --input data/input/synthetic_complex.dxf \
  --output data/output/demo_debug.png
```

Open `demo_debug.png`:
- Gray: site boundary
- Red: forbidden zones
- Green: allowed area
- Orange/brown/gray: communications, buildings, roads
- Green dots: accepted plantings

---

## Step 6: Open Output DXF (1 min)

Open `data/output/demo_result.dxf` in LibreCAD / AutoCAD / sharecad.org.

Show:
- Original layers unchanged (SITE, PIPE, WATER, GAS, BUILDINGS, ROADS)
- New layers: **PLANTING_TREES**, **PLANTING_SHRUBS**, **PLANTING_PROPOSED**
- Plantings outside communication buffers

---

## Step 7: Validate Output (30 sec)

```bash
green-planner validate --input data/output/demo_result.dxf
```

Confirm planting layers present.

---

## Step 8: Interpretation Report (2 min)

```bash
green-planner report --input data/output/interpretation.json
```

Open `data/output/interpretation.json` and pick one planting:

```json
{
  "id": "tree_001",
  "type": "tree",
  "x": 43.73,
  "y": 28.63,
  "status": "accepted",
  "distances": {
    "communication": 25.0,
    "building": 40.0
  },
  "checks": [{
    "rule": "communication_distance",
    "value": 25.0,
    "required": 2.0,
    "status": "passed",
    "regulation": "743-ПП",
    "clause": "TODO_VERIFY"
  }],
  "explanation": "Посадка типа tree допустима: ..."
}
```

Show:
- Coordinates
- Distance to communication
- Applied rule and required minimum
- Regulation document: **743-ПП**
- Clause: **TODO_VERIFY** (needs expert verification)

---

## Step 9: Repeat with Different Parameter (1 min)

Create a limited config:

```bash
cp config/default.yaml config/demo_limited.yaml
```

Edit `demo_limited.yaml`:
```yaml
planting:
  tree:
    max_count: 10
  shrub:
    enabled: false
```

Re-run:
```bash
green-planner process \
  --input data/input/synthetic_complex.dxf \
  --output data/output/demo_limited.dxf \
  --config config/demo_limited.yaml
```

Show: tree count ≤ 10, shrubs disabled.

---

## Step 10: Docker (optional, 1 min)

```bash
docker build -t green-planner .
docker run --rm \
  -v ./data:/app/data \
  -v ./config:/app/config \
  green-planner process \
  --input /app/data/input/test.dxf \
  --output /app/data/output/docker_result.dxf
```

See `docs/DOCKER_TEST.md` for full instructions.

---

## Key Messages

1. **Deterministic** — same input + config → same output
2. **Non-destructive** — source DXF layers never modified
3. **Explainable** — every planting has checks, distances, regulation refs
4. **Configurable** — layers, distances, density limits via YAML
5. **Honest about norms** — unverified clauses marked `TODO_VERIFY`
