# Docker Test Instructions

## Status

Docker image has **not been runtime-tested** on the development machine
(`docker: command not found`). The Dockerfile has been verified statically
for Linux compatibility.

## Static Verification Checklist

| Item | Status |
|------|--------|
| Base image: `python:3.11-slim` | ✅ |
| GEOS dependency: `libgeos-dev` | ✅ |
| Non-root WORKDIR `/app` | ✅ |
| Volume mount `/app/data` | ✅ |
| CLI entrypoint `green-planner` | ✅ |
| Editable install via `pip install -e .` | ✅ |

## Build

```bash
docker build -t green-planner .
```

Expected: image builds without errors.

## Run Full E2E Pipeline

```bash
# Ensure test DXF exists
python scripts/create_test_dxf.py
python scripts/create_complex_dxf.py

docker run --rm \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/config:/app/config" \
  green-planner \
  inspect \
  --input /app/data/input/synthetic_complex.dxf

docker run --rm \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/config:/app/config" \
  green-planner \
  process \
  --input /app/data/input/synthetic_complex.dxf \
  --output /app/data/output/docker_result.dxf \
  --config /app/config/default.yaml

docker run --rm \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/config:/app/config" \
  green-planner \
  validate \
  --input /app/data/output/docker_result.dxf
```

## Expected Output Files

After successful run inside container:

```
data/output/
├── docker_result.dxf
├── interpretation.json
└── run_report.json
```

## Verify Source Layer Integrity

```bash
docker run --rm \
  -v "$(pwd)/data:/app/data" \
  green-planner \
  inspect --input /app/data/output/docker_result.dxf
```

Original layers (SITE, PIPE, BUILDINGS, ROADS) must have same entity counts
as input. New layers (PLANTING_*) must appear.

## Docker Compose

```bash
docker compose run --rm green-planner process \
  --input /app/data/input/test.dxf \
  --output /app/data/output/result.dxf
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `libgeos` errors | Ensure `libgeos-dev` is installed in Dockerfile |
| Permission denied on `/app/data` | Check volume mount permissions |
| Config not found | Mount `./config:/app/config` |
| No communication layers | Edit `config/default.yaml` layer mapping |

## Target Environment

Test on:
- Ubuntu 22.04+
- MosTech OS compatible Linux environment
