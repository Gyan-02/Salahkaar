from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_analysis_pipeline
from app.api.pipeline import AnalysisPipeline
from app.schemas.api import AnalysisRunRequest
from app.schemas.engine import ReadinessResult, RiskResult


router = APIRouter(tags=["readiness", "risk"])
PipelineDependency = Annotated[AnalysisPipeline, Depends(get_analysis_pipeline)]


@router.post("/readiness/check", response_model=ReadinessResult)
async def check_readiness(
    request: AnalysisRunRequest,
    pipeline: PipelineDependency,
) -> ReadinessResult:
    return (await pipeline.run(request)).readiness


@router.post("/risk/check", response_model=RiskResult)
async def check_risk(
    request: AnalysisRunRequest,
    pipeline: PipelineDependency,
) -> RiskResult:
    return (await pipeline.run(request)).risk

