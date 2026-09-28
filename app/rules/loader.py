"""Load rules from configuration."""

from __future__ import annotations

import json
from pathlib import Path

from app.config import AppConfig
from app.rules.models import PlantingRule, RulesCatalog


def load_rules_from_config(config: AppConfig) -> RulesCatalog:
    """Build rules catalog from application configuration."""
    rules: list[PlantingRule] = []

    for planting_type in config.planting:
        type_rules = config.get_type_rules(planting_type)
        for restriction_type, rule in [
            ("communication", type_rules.communication),
            ("building", type_rules.building),
            ("road", type_rules.road),
        ]:
            if rule is None:
                continue
            rules.append(
                PlantingRule(
                    planting_type=planting_type,
                    restriction_type=restriction_type,
                    minimum_distance=rule.minimum_distance,
                    regulation_document=rule.regulation.document,
                    regulation_clause=rule.regulation.clause,
                    explanation_template=rule.regulation.description,
                    priority=_priority_for(restriction_type),
                )
            )

    return RulesCatalog(rules=rules)


def load_default_rules_json() -> dict:
    """Load bundled default rules JSON."""
    path = Path(__file__).parent / "default_rules.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _priority_for(restriction_type: str) -> int:
    priorities = {"communication": 3, "building": 2, "road": 1}
    return priorities.get(restriction_type, 0)
