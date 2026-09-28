# Normative Verification Status

This document separates **technically implemented rules** (enforced by the engine)
from **normative data requiring expert confirmation**.

## Technically Implemented Rules

These rules are active in `config/default.yaml` and enforced deterministically
by `app/rules/engine.py` and `app/geometry/buffers.py`:

| Rule | Implementation | Config Key | Enforced By |
|------|---------------|------------|-------------|
| Communication buffer zone | Buffer around comm. geometry | `rules.communication.default_buffer` | `geometry/buffers.py` |
| Tree → communication distance | Point distance check | `rules.tree.communication.minimum_distance` | `rules/engine.py` |
| Tree → building distance | Point distance check | `rules.tree.building.minimum_distance` | `rules/engine.py` |
| Tree → road distance | Point distance check | `rules.tree.road.minimum_distance` | `rules/engine.py` |
| Shrub → communication distance | Point distance check | `rules.shrub.communication.minimum_distance` | `rules/engine.py` |
| Shrub → building distance | Point distance check | `rules.shrub.building.minimum_distance` | `rules/engine.py` |
| Shrub → road distance | Point distance check | `rules.shrub.road.minimum_distance` | `rules/engine.py` |
| Tree minimum spacing | Inter-planting distance | `planting.tree.min_spacing` | `rules/engine.py` |
| Shrub minimum spacing | Inter-planting distance | `planting.shrub.min_spacing` | `rules/engine.py` |
| Max planting count | Greedy cap | `planting.*.max_count` | `planting/optimizer.py` |
| Target density | Greedy cap per 1000 m² | `planting.*.target_density` | `planting/optimizer.py` |

## Normative Data Requiring Expert Verification

| Rule | Document | Clause | Status |
|------|----------|--------|--------|
| Communication buffer zone | 743-ПП | TODO_VERIFY | needs expert verification |
| Tree → communication distance (2.0 m) | 743-ПП | TODO_VERIFY | needs expert verification |
| Tree → building distance (5.0 m) | СП 42.13330.2016 | TODO_VERIFY | needs expert verification |
| Tree → road distance (3.0 m) | 623-ПП | TODO_VERIFY | needs expert verification |
| Shrub → communication distance (1.0 m) | 743-ПП | TODO_VERIFY | needs expert verification |
| Shrub → building distance (2.0 m) | СП 42.13330.2016 | TODO_VERIFY | needs expert verification |
| Shrub → road distance (1.5 m) | 623-ПП | TODO_VERIFY | needs expert verification |
| Tree minimum spacing (6.0 m) | СП 42.13330.2016 | TODO_VERIFY | needs expert verification |
| Shrub minimum spacing (2.0 m) | СП 42.13330.2016 | TODO_VERIFY | needs expert verification |
| General planting requirements | МГСН | TODO_VERIFY | needs expert verification |

## Referenced Normative Documents

| ID | Title | Role in MVP |
|----|-------|-------------|
| СП 42.13330.2016 | Градостроительство. Планировка и застройка | Building distances, spacing |
| 743-ПП | Постановление Правительства Москвы №743-ПП | Communication distances, buffers |
| 623-ПП | Постановление Правительства Москвы №623-ПП | Road distances |
| МГСН | Московские городские строительные нормы | General requirements (not configured) |

## How to Verify

1. Domain expert reviews each `TODO_VERIFY` entry against official document text.
2. Update `config/default.yaml` with confirmed values and clause references.
3. Re-run pipeline — no code changes required.
4. Update this document, changing Status from `needs expert verification` to `verified`.

## Important

- The system **does not invent** normative clause numbers.
- Hard constraint decisions are **deterministic** and do not use AI/LLM.
- All unverified clauses appear as `TODO_VERIFY` in `interpretation.json`.
