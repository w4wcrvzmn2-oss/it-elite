# Algorithm

## 1. DXF Reading

The reader opens the DXF via `ezdxf` and iterates modelspace entities. Supported types are converted to Shapely geometries:

| DXF Type | Shapely Geometry |
|----------|-----------------|
| LINE | LineString |
| LWPOLYLINE | LineString or Polygon (if closed) |
| POLYLINE | LineString or Polygon (if closed) |
| CIRCLE | Polygon (buffered point) |
| ARC | Polygon (buffered point, simplified) |
| POINT | Point |
| INSERT | Point (at insert location) |

Each entity becomes a `GeometryObject` with id, layer, type, geometry, and metadata.

## 2. Layer Classification

Layer names from the DXF are matched against configured patterns in `config/default.yaml`:

```yaml
layers:
  communications: [PIPE, WATER, GAS, ...]
  buildings: [BUILDINGS, BUILDING]
  roads: [ROADS, ROAD]
  boundary: [SITE, BOUNDARY]
```

Matching is case-insensitive and supports substring matching (e.g., "PIPE" matches layer "WATER_PIPE").

## 3. Buffer Creation

For each restriction category, all geometries are collected and a unified buffer is created:

```
buffer = unary_union([geom.buffer(distance) for geom in category_geometries])
```

Buffer distances come from config:
- Communications: `rules.communication.default_buffer` (default 2.0m)
- Buildings: max of all planting type building distances
- Roads: max of all planting type road distances

## 4. Allowed Area

```
allowed_area = planting_boundary.difference(forbidden_zone)
```

Where `planting_boundary` is the largest polygon from boundary layer, or convex hull fallback.

Invalid geometries are repaired with `shapely.make_valid` before operations.

## 5. Candidate Point Generation

A regular grid is generated over the allowed area bounding box:

```python
xs = arange(minx + step/2, maxx, step)
ys = arange(miny + step/2, maxy, step)
```

Grid step is configurable per planting type (`candidate_grid_step`). Points outside the allowed area are filtered using prepared geometry (`prep.contains`).

A small random offset (seeded) prevents grid alignment artifacts.

## 6. Point Selection (Greedy Optimization)

1. Score each candidate point based on:
   - Distance to restrictions (farther = better)
   - Distance to area centroid (closer to center = slightly better)
2. Sort candidates by score (descending)
3. Iterate and accept if all hard constraints pass:
   - Inside allowed area
   - Distance to communications ≥ minimum
   - Distance to buildings ≥ minimum
   - Distance to roads ≥ minimum
   - Distance to accepted plantings ≥ min_spacing

Hard constraints are never overridden by score.

## 7. Constraint Checking

The rules engine uses Shapely STRtree for efficient nearest-neighbor queries:

```python
distance = point.distance(nearest_restriction_geometry)
passed = distance >= rule.minimum_distance
```

Each check produces an `AppliedRule` with value, required, status, regulation document, and clause.

## 8. Final Validation

Before export, every accepted planting is re-validated against all hard constraints. Any planting that fails is removed.

## 9. Explanation Generation

For each accepted planting, a Russian-language explanation is built from passed checks:

```
"Посадка типа tree допустима: расстояние до communication составляет 30.0 м 
при требовании ≥ 2.0 м (743-ПП, TODO_VERIFY); ..."
```

## 10. DXF Export

The source DXF is loaded unchanged. New entities are added:
- CIRCLE on type-specific layer (PLANTING_TREES / PLANTING_SHRUBS)
- POINT on PLANTING_PROPOSED layer

Source layer entity counts are verified before and after.

## Complexity

- Grid generation: O(n) where n = (width/step) × (height/step)
- Greedy selection: O(c × r) where c = candidates, r = rules
- Spatial queries: O(log m) per query via STRtree, m = restriction geometries
- Overall: approximately O(c × r × log m), avoiding O(c²) pairwise checks
