from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_analysis_pipeline
from app.api.pipeline import AnalysisPipeline
from app.schemas.api import AnalysisRunRequest
from app.schemas.engine import ActionPlanResult


router = APIRouter(tags=["action-plan"])
PipelineDependency = Annotated[AnalysisPipeline, Depends(get_analysis_pipeline)]


@router.post("/action-plan", response_model=ActionPlanResult)
async def create_action_plan(
    request: AnalysisRunRequest,
    pipeline: PipelineDependency,
) -> ActionPlanResult:
    return (await pipeline.run(request)).action_plan

