"""Rules engine for constraint checking."""

from __future__ import annotations

from shapely.geometry.base import BaseGeometry

from app.geometry.points import build_strtree, min_distance_to_geometries
from app.rules.models import AppliedRule, PlantingRule, RulesCatalog


class RulesEngine:
    """Evaluate planting points against normative rules."""

    def __init__(
        self,
        catalog: RulesCatalog,
        restriction_geometries: dict[str, list[BaseGeometry]],
    ) -> None:
        self.catalog = catalog
        self.restriction_geometries = restriction_geometries
        self._trees: dict[str, object] = {}
        for category, geoms in restriction_geometries.items():
            self._trees[category] = build_strtree(geoms)

    def check_point(
        self,
        point: tuple[float, float],
        planting_type: str,
        existing_plantings: list[tuple[float, float]] | None = None,
        min_spacing: float | None = None,
    ) -> tuple[bool, list[AppliedRule]]:
        """Check a point against all applicable rules. Returns (valid, checks)."""
        checks: list[AppliedRule] = []
        all_passed = True

        type_rules = self.catalog.get_rules_for_type(planting_type)
        for rule in sorted(type_rules, key=lambda r: -r.priority):
            geoms = self.restriction_geometries.get(rule.restriction_type, [])
            tree = self._trees.get(rule.restriction_type)
            distance = min_distance_to_geometries(point, geoms, tree=tree)  # type: ignore[arg-type]

            if not geoms:
                checks.append(
                    AppliedRule(
                        rule=f"{rule.restriction_type}_distance",
                        value=None,
                        required=rule.minimum_distance,
                        status="skipped",
                        regulation=rule.regulation_document,
                        clause=rule.regulation_clause,
                        description=f"No {rule.restriction_type} geometries detected",
                    )
                )
                continue

            passed = distance >= rule.minimum_distance
            if not passed:
                all_passed = False

            checks.append(
                AppliedRule(
                    rule=f"{rule.restriction_type}_distance",
                    value=round(distance, 2),
                    required=rule.minimum_distance,
                    status="passed" if passed else "failed",
                    regulation=rule.regulation_document,
                    clause=rule.regulation_clause,
                    description=rule.explanation_template,
                )
            )

        if min_spacing is not None and existing_plantings:
            from app.geometry.points import min_distance_between_points

            spacing = min_distance_between_points(point, existing_plantings)
            passed = spacing >= min_spacing
            if not passed:
                all_passed = False
            checks.append(
                AppliedRule(
                    rule="minimum_spacing",
                    value=round(spacing, 2),
                    required=min_spacing,
                    status="passed" if passed else "failed",
                    regulation="CONFIG",
                    clause="planting.min_spacing",
                    description=f"Minimum spacing between {planting_type} plantings",
                )
            )

        return all_passed, checks

    def get_buffer_distances(self, config_buffers: dict[str, float]) -> dict[str, float]:
        """Return buffer distances for forbidden zone construction."""
        return config_buffers
