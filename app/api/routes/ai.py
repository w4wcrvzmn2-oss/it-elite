"""AI API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.ai.schemas import (
    AIAskResponse,
    AIExplanation,
    AIReport,
    AIStatusResponse,
    AISiteSummary,
    AskRequest,
    CompareScenariosRequest,
    ExplainPlantingRequest,
    ReportRequest,
    ScenarioComparisonAI,
    SitePassport,
    SiteSummaryRequest,
    VisualizationPromptRequest,
    VisualizationPromptResponse,
    WhyNotRequest,
)
from app.ai.service import (
    ask_question,
    compare_scenarios_ai,
    explain_planting,
    generate_passport,
    generate_report,
    generate_site_summary,
    get_ai_status,
)
from app.analysis.why_not import explain_why_not_here
from app.scenarios.service import load_scenarios_from_disk
from app.api.jobs import JobStatus, get_job_store
from app.interpretation.generator import load_interpretation

router = APIRouter(prefix="/api/ai", tags=["AI"])


@router.get("/status", response_model=AIStatusResponse)
def ai_status() -> AIStatusResponse:
    s = get_ai_status()
    return AIStatusResponse(**s)


@router.post("/explain-planting", response_model=AIExplanation)
def api_explain_planting(request: ExplainPlantingRequest) -> AIExplanation:
    store = get_job_store()
    job = store.get_job(request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")

    planting = None
    interp_path = job.output_dir / "interpretation.json"
    if interp_path.exists():
        report = load_interpretation(interp_path)
        for p in report.plantings:
            if p.id == request.planting_id:
                planting = p.model_dump()
                break

    if not planting and job.result:
        for p in job.result.accepted_plantings:
            if p.id == request.planting_id:
                planting = {
                    "id": p.id,
                    "type": p.planting_type,
                    "x": p.x,
                    "y": p.y,
                    "status": p.status,
                    "checks": [c.model_dump() if hasattr(c, "model_dump") else c.__dict__ for c in p.checks],
                    "distances": {},
                    "explanation": p.explanation,
                }
                break

    if not planting:
        raise HTTPException(status_code=404, detail="Planting not found")

    return explain_planting(planting)


@router.post("/site-summary", response_model=AISiteSummary)
def api_site_summary(request: SiteSummaryRequest) -> AISiteSummary:
    store = get_job_store()
    job = store.get_job(request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")

    stats = dict(job.run_report)
    stats["job_id"] = request.job_id
    rules = stats.get("rules_applied", [])
    return generate_site_summary(stats, rules)


@router.post("/ask", response_model=AIAskResponse)
def api_ask(request: AskRequest) -> AIAskResponse:
    store = get_job_store()
    job = store.get_job(request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")

    stats = job.run_report
    plantings_sample = []
    if job.result:
        plantings_sample = [
            {"id": p.id, "type": p.planting_type, "x": p.x, "y": p.y}
            for p in job.result.accepted_plantings[:20]
        ]

    context = {
        "statistics": stats,
        "plantings_sample": plantings_sample,
        "rules_applied": stats.get("rules_applied", [])[:10],
        "communications": stats.get("communications", 0),
    }

    return ask_question(request.job_id, request.question, context)


@router.post("/report", response_model=AIReport)
def api_report(request: ReportRequest) -> AIReport:
    store = get_job_store()
    job = store.get_job(request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")

    stats = dict(job.run_report)
    stats["job_id"] = request.job_id
    rules = stats.get("rules_applied", [])
    sample = []
    if job.result:
        sample = [{"id": p.id, "type": p.planting_type, "x": p.x, "y": p.y} for p in job.result.accepted_plantings[:10]]

    return generate_report(stats, rules, sample)


@router.post("/compare-scenarios", response_model=ScenarioComparisonAI)
def api_compare_scenarios(request: CompareScenariosRequest) -> ScenarioComparisonAI:
    store = get_job_store()
    job = store.get_job(request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    scenarios = load_scenarios_from_disk(job.output_dir)
    if not scenarios:
        raise HTTPException(status_code=400, detail="Сценарии не рассчитаны")
    return compare_scenarios_ai(request.job_id, scenarios)


@router.post("/passport", response_model=SitePassport)
def api_passport(request: ReportRequest) -> SitePassport:
    store = get_job_store()
    job = store.get_job(request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    stats = dict(job.run_report)
    stats["job_id"] = request.job_id
    return generate_passport(stats, stats.get("rules_applied", []))


@router.post("/why-not")
def api_why_not(request: WhyNotRequest) -> dict:
    store = get_job_store()
    job = store.get_job(request.job_id)
    if not job or job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Job not found")
    interp = job.output_dir / "interpretation.json"
    if not interp.exists():
        raise HTTPException(status_code=404, detail="Interpretation not found")
    return explain_why_not_here(request.x, request.y, interp, job.run_report)


@router.post("/visualization-prompt", response_model=VisualizationPromptResponse)
def api_viz_prompt(request: VisualizationPromptRequest) -> VisualizationPromptResponse:
    store = get_job_store()
    job = store.get_job(request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    stats = job.run_report
    types = stats.get("planting_types", {})
    desc = {
        "trees": types.get("tree", 0),
        "shrubs": types.get("shrub", 0),
        "allowed_area_m2": stats.get("allowed_area_m2"),
        "site_area_m2": stats.get("site_area_m2"),
    }
    prompt = (
        f"Визуализация городского двора после озеленения: {desc['trees']} деревьев, "
        f"{desc['shrubs']} кустарников. Сохранить структуру участка."
    )
    return VisualizationPromptResponse(description=desc, prompt=prompt)
