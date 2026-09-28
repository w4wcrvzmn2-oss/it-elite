"""Planting data models."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.rules.models import AppliedRule


@dataclass
class PlantingPoint:
    """A single planting location."""

    id: str
    planting_type: str
    x: float
    y: float
    status: str = "accepted"
    score: float = 0.0
    checks: list[AppliedRule] = field(default_factory=list)
    explanation: str = ""


@dataclass
class RejectedPoint:
    """A rejected candidate planting location."""

    x: float
    y: float
    planting_type: str
    reason: str
    distance: float | None = None
    required: float | None = None
    regulation: str = ""
    clause: str = "TODO_VERIFY"


@dataclass
class PlantingResult:
    """Result of planting generation."""

    accepted: list[PlantingPoint]
    rejected: list[RejectedPoint]
    candidate_count: int
    allowed_area: float
    forbidden_area: float
