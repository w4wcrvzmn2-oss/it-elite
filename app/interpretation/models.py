"""Interpretation report models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CheckResult(BaseModel):
    rule: str
    value: float | None = None
    required: float
    status: str
    regulation: str
    clause: str = "TODO_VERIFY"
    description: str = ""


class PlantingInterpretation(BaseModel):
    id: str
    type: str
    x: float
    y: float
    status: str
    score: float = 0.0
    checks: list[CheckResult] = Field(default_factory=list)
    distances: dict[str, float | None] = Field(default_factory=dict)
    explanation: str = ""


class RejectedInterpretation(BaseModel):
    x: float
    y: float
    type: str
    status: str = "rejected"
    reason: str
    distance: float | None = None
    required: float | None = None
    regulation: str = ""
    clause: str = "TODO_VERIFY"


class InterpretationReport(BaseModel):
    plantings: list[PlantingInterpretation] = Field(default_factory=list)
    rejected: list[RejectedInterpretation] = Field(default_factory=list)
    rules_applied: list[dict] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)
