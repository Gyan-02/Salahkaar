from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_analysis_pipeline
from app.api.pipeline import AnalysisPipeline
from app.engines.program_registry import ProgramNotFoundError
from app.schemas.program import ProgramDefinition


router = APIRouter(prefix="/programs", tags=["programs"])
PipelineDependency = Annotated[AnalysisPipeline, Depends(get_analysis_pipeline)]


@router.get("", response_model=list[ProgramDefinition])
def list_programs(pipeline: PipelineDependency) -> list[ProgramDefinition]:
    return pipeline.registry.list_programs()


@router.get("/{program_id}", response_model=ProgramDefinition)
def get_program(program_id: str, pipeline: PipelineDependency) -> ProgramDefinition:
    try:
        return pipeline.registry.get_program(program_id)
    except ProgramNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

