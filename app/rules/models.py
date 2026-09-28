"""Rule data models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PlantingRule(BaseModel):
    """A single normative planting restriction rule."""

    planting_type: str
    restriction_type: str
    minimum_distance: float
    regulation_document: str
    regulation_clause: str = "TODO_VERIFY"
    explanation_template: str = ""
    priority: int = 0


class AppliedRule(BaseModel):
    """Record of an applied rule during validation."""

    rule: str
    value: float | None = None
    required: float
    status: str  # passed | failed
    regulation: str
    clause: str = "TODO_VERIFY"
    description: str = ""


class RulesCatalog(BaseModel):
    """Collection of all active rules."""

    rules: list[PlantingRule] = Field(default_factory=list)

    def get_rules_for_type(self, planting_type: str) -> list[PlantingRule]:
        return [r for r in self.rules if r.planting_type == planting_type]

    def to_report(self) -> list[dict]:
        return [
            {
                "planting_type": r.planting_type,
                "restriction_type": r.restriction_type,
                "minimum_distance": r.minimum_distance,
                "regulation_document": r.regulation_document,
                "regulation_clause": r.regulation_clause,
                "explanation_template": r.explanation_template,
                "priority": r.priority,
            }
            for r in self.rules
        ]
