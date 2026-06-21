from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_analysis_pipeline
from app.api.pipeline import AnalysisPipeline
from app.schemas.api import DocumentsCheckRequest
from app.schemas.engine import ContradictionResult


router = APIRouter(tags=["contradictions"])
PipelineDependency = Annotated[AnalysisPipeline, Depends(get_analysis_pipeline)]


@router.post("/contradictions/check", response_model=ContradictionResult)
def check_contradictions(
    request: DocumentsCheckRequest,
    pipeline: PipelineDependency,
) -> ContradictionResult:
    profile = pipeline.profile_builder.build(request.documents)
    return pipeline.contradiction_engine.check(profile)
