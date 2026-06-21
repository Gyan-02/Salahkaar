import json
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_analysis_pipeline
from app.api.pipeline import AnalysisPipeline
from app.api.persistence import persist_execution
from app.config.database import get_db
from app.config.paths import DATA_PATH
from app.schemas.analysis import AnalysisResult
from app.schemas.api import AnalysisRunRequest, DemoCaseResponse


router = APIRouter(tags=["analysis", "demo"])
PipelineDependency = Annotated[AnalysisPipeline, Depends(get_analysis_pipeline)]
SessionDependency = Annotated[Session, Depends(get_db)]


@router.post("/analysis/run", response_model=AnalysisResult)
async def run_analysis(
    request: AnalysisRunRequest,
    pipeline: PipelineDependency,
    session: SessionDependency,
) -> AnalysisResult:
    execution = await pipeline.run(request)
    persist_execution(execution, session)
    return execution.result


@router.post("/demo/run/{case_id}", response_model=DemoCaseResponse)
async def run_demo_case(
    case_id: str,
    pipeline: PipelineDependency,
    session: SessionDependency,
) -> DemoCaseResponse:
    case = _get_demo_case(case_id)
    request = AnalysisRunRequest(
        program_id=case["program_id"],
        documents=case["documents"],
        answers=case.get("answers", {}),
        document_quality=case.get("document_quality", []),
    )
    execution = await pipeline.run(request)
    persist_execution(execution, session)
    return DemoCaseResponse(
        case_id=case_id,
        **execution.result.model_dump(mode="python"),
    )


def _get_demo_case(case_id: str) -> dict[str, Any]:
    path = Path(DATA_PATH) / "mock_cases.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    case = next((item for item in payload["cases"] if item["id"] == case_id), None)
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown demo case: {case_id}",
        )
    return case
