from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_analysis_pipeline
from app.api.pipeline import AnalysisPipeline
from app.schemas.api import AnalysisRunRequest, QuestionsResponse
from app.schemas.engine import EligibilityResult


router = APIRouter(tags=["eligibility"])
PipelineDependency = Annotated[AnalysisPipeline, Depends(get_analysis_pipeline)]


@router.post("/questions/generate", response_model=QuestionsResponse)
async def generate_questions(
    request: AnalysisRunRequest,
    pipeline: PipelineDependency,
) -> QuestionsResponse:
    execution = await pipeline.run(request)
    return QuestionsResponse(questions=execution.eligibility.questions)


@router.post("/eligibility/check", response_model=EligibilityResult)
async def check_eligibility(
    request: AnalysisRunRequest,
    pipeline: PipelineDependency,
) -> EligibilityResult:
    return (await pipeline.run(request)).eligibility

