# Normative Logic

## Referenced Documents

| Document | Description |
|----------|-------------|
| СП 42.13330.2016 | Градостроительство. Планировка и застройка городских и сельских поселений |
| Постановление Правительства Москвы №743-ПП | Требования к озеленению территории |
| Постановление Правительства Москвы №623-ПП | Требования к благоустройству |
| МГСН | Московские городские строительные нормы |

## Configuration Structure

All normative values are stored in `config/default.yaml` under the `rules` section:

```yaml
rules:
  tree:
    communication:
      minimum_distance: 2.0
      regulation:
        document: "743-ПП"
        clause: "TODO_VERIFY"
        description: "Минимальный отступ от коммуникаций для деревьев"
```

## Applied Rules (MVP defaults)

| Planting Type | Restriction | Distance (m) | Document | Clause |
|---------------|-------------|-------------|----------|--------|
| tree | communication | 2.0 | 743-ПП | TODO_VERIFY |
| tree | building | 5.0 | СП 42.13330.2016 | TODO_VERIFY |
| tree | road | 3.0 | 623-ПП | TODO_VERIFY |
| shrub | communication | 1.0 | 743-ПП | TODO_VERIFY |
| shrub | building | 2.0 | СП 42.13330.2016 | TODO_VERIFY |
| shrub | road | 1.5 | 623-ПП | TODO_VERIFY |
| all | communication buffer | 2.0 | 743-ПП | TODO_VERIFY |

## Spacing Rules

| Planting Type | Min Spacing (m) | Source |
|---------------|----------------|--------|
| tree | 6.0 | config (TODO_VERIFY against SP 42.13330.2016) |
| shrub | 2.0 | config (TODO_VERIFY) |

## How Rules Are Applied

1. **Buffer zones** (forbidden areas): Created from communication/building/road geometries using configured buffer distances. These define WHERE planting is physically impossible.

2. **Distance checks** (per-point validation): Each candidate point is checked against nearest restriction geometry. The actual measured distance must exceed the configured minimum.

3. **Spacing checks**: Between accepted plantings of the same type, minimum spacing is enforced.

4. **Regulation references**: Every check records the source document and clause. Unverified clauses are marked `TODO_VERIFY`.

## Normative Data Requiring Expert Verification

The following values are configured as reasonable defaults but **must be verified by a domain expert** before production use:

1. **743-ПП** — minimum distance from communications for trees (2.0m) — `TODO_VERIFY`
2. **743-ПП** — minimum distance from communications for shrubs (1.0m) — `TODO_VERIFY`
3. **743-ПП** — communication buffer zone (2.0m) — `TODO_VERIFY`
4. **СП 42.13330.2016** — minimum distance from buildings for trees (5.0m) — `TODO_VERIFY`
5. **СП 42.13330.2016** — minimum distance from buildings for shrubs (2.0m) — `TODO_VERIFY`
6. **623-ПП** — minimum distance from roads for trees (3.0m) — `TODO_VERIFY`
7. **623-ПП** — minimum distance from roads for shrubs (1.5m) — `TODO_VERIFY`
8. **СП 42.13330.2016** — minimum tree spacing (6.0m) — `TODO_VERIFY`
9. **МГСН** — specific planting requirements — `TODO_VERIFY`

## Updating Normative Values

To update a normative value after expert verification:

1. Edit `config/default.yaml`
2. Change the `minimum_distance` value
3. Replace `"clause": "TODO_VERIFY"` with the verified clause reference
4. Re-run the pipeline — no code changes needed

Example after verification:
```yaml
communication:
  minimum_distance: 2.5
  regulation:
    document: "743-ПП"
    clause: "п. 4.2.1, табл. 3"
    description: "Минимальный отступ от подземных коммуникаций"
```

## Important Notes

- The system does NOT invent normative clause numbers
- All unverified references use `TODO_VERIFY`
- Hard constraint decisions are deterministic and do not depend on AI/LLM
- The rules engine is fully configurable via YAML
