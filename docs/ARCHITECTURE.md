# Architecture

## Pipeline Overview

```
DXF File
  ↓
[DXF Reader]           app/dxf/reader.py
  ↓
[Layer Classification] app/pipeline.py + app/config.py
  ↓
[Geometry Normalization] app/geometry/validation.py
  ↓
[Rules Engine]         app/rules/engine.py
  ↓
[Forbidden Zones]      app/geometry/buffers.py
  ↓
[Allowed Area]         app/geometry/buffers.py
  ↓
[Candidate Generation] app/planting/generator.py
  ↓
[Optimization]         app/planting/optimizer.py
  ↓
[Validation]           app/planting/validator.py
  ↓
[Interpretation]       app/interpretation/generator.py
  ↓
[DXF Writer]           app/dxf/writer.py
  ↓
[JSON Reports]         interpretation.json, run_report.json
```

## Module Responsibilities

### `app/dxf/`
- **reader.py** — Parse DXF entities (LINE, LWPOLYLINE, POLYLINE, CIRCLE, ARC, POINT, INSERT) into unified `GeometryObject` model
- **writer.py** — Write planting entities to new layers without modifying source layers
- **layers.py** — Layer statistics and entity counting
- **entities.py** — Data models: `GeometryObject`, `LayerInfo`, `DxfDocument`

### `app/geometry/`
- **buffers.py** — Buffer creation, forbidden zone union, allowed area calculation
- **polygons.py** — Geometry merging, bounding box, largest polygon extraction
- **points.py** — Grid generation, spatial indexing (STRtree), distance calculations
- **validation.py** — Invalid geometry repair via `make_valid`

### `app/rules/`
- **models.py** — `PlantingRule`, `AppliedRule`, `RulesCatalog`
- **engine.py** — Point validation against normative rules
- **loader.py** — Load rules from YAML config
- **default_rules.json** — Bundled normative document references

### `app/planting/`
- **generator.py** — Regular grid candidate point generation
- **optimizer.py** — Greedy selection with scoring
- **validator.py** — Final hard-constraint validation before export
- **models.py** — `PlantingPoint`, `RejectedPoint`, `PlantingResult`

### `app/interpretation/`
- **generator.py** — Build and save JSON interpretation reports
- **models.py** — Pydantic models for report structure

### `app/pipeline.py`
Orchestrates the full processing flow. Handles error cases (missing layers, empty allowed area, source layer integrity verification).

### `app/cli.py`
Typer-based CLI with commands: `inspect`, `process`, `validate`, `report`, `debug`.

### `app/config.py`
Pydantic models for YAML configuration. Layer matching, rule loading, planting type parameters.

## Data Flow

1. DXF entities → `GeometryObject` list with Shapely geometries
2. Layer names matched against config patterns → categorized geometries
3. Category buffers merged → `forbidden_zone`
4. `planting_boundary - forbidden_zone` → `allowed_area`
5. Grid points in allowed area → candidates
6. Greedy filter by rules + spacing → accepted/rejected
7. Final validation → export to DXF + JSON

## Design Principles

- **Deterministic**: Same input + config + seed → same output
- **Configurable**: No hardcoded layer names or distances
- **Non-destructive**: Source DXF layers never modified
- **Explainable**: Every planting has rule checks with regulation references
- **Verifiable**: `TODO_VERIFY` marks unconfirmed normative clauses
