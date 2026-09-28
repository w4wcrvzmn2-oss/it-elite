"""AI response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AIExplanation(BaseModel):
    title: str = "Объяснение посадки"
    summary: str = ""
    reasons: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    regulatory_notes: list[str] = Field(default_factory=list)
    verification_notes: list[str] = Field(default_factory=list)
    ai_generated: bool = True
    fallback: bool = False


class AISiteSummary(BaseModel):
    title: str = "Анализ участка"
    summary: str = ""
    key_metrics: list[str] = Field(default_factory=list)
    restrictions_overview: str = ""
    planting_overview: str = ""
    ai_generated: bool = True
    fallback: bool = False


class AIAskResponse(BaseModel):
    answer: str = ""
    ai_generated: bool = True
    fallback: bool = False


class AIReportSection(BaseModel):
    title: str
    content: str


class AIReport(BaseModel):
    title: str = "AI Planting Report"
    overview: str = ""
    sections: list[AIReportSection] = Field(default_factory=list)
    regulatory_notes: list[str] = Field(default_factory=list)
    verification_notes: list[str] = Field(default_factory=list)
    ai_generated: bool = True
    fallback: bool = False


class ExplainPlantingRequest(BaseModel):
    job_id: str
    planting_id: str


class SiteSummaryRequest(BaseModel):
    job_id: str


class AskRequest(BaseModel):
    job_id: str
    question: str


class ReportRequest(BaseModel):
    job_id: str


class AIStatusResponse(BaseModel):
    enabled: bool
    available: bool
    model: str | None = None
    message: str = ""
    last_latency_sec: float | None = None
    last_tokens: int | None = None


class ScenarioComparisonAI(BaseModel):
    summary: str = ""
    scenario_summaries: list[dict] = Field(default_factory=list)
    differences: list[str] = Field(default_factory=list)
    metrics_notes: list[str] = Field(default_factory=list)
    verification_notes: list[str] = Field(default_factory=list)
    ai_generated: bool = True
    fallback: bool = False


class SitePassport(BaseModel):
    title: str = "Паспорт участка"
    sections: list[AIReportSection] = Field(default_factory=list)
    regulatory_notes: list[str] = Field(default_factory=list)
    verification_notes: list[str] = Field(default_factory=list)
    executive_summary: str = ""
    ai_generated: bool = True
    fallback: bool = False


class CompareScenariosRequest(BaseModel):
    job_id: str


class WhyNotRequest(BaseModel):
    job_id: str
    x: float
    y: float


class VisualizationPromptRequest(BaseModel):
    job_id: str


class VisualizationPromptResponse(BaseModel):
    description: dict = Field(default_factory=dict)
    prompt: str = ""
    ai_generated: bool = False
    fallback: bool = False
