import pytest

from app.engines.action_planner import ActionPlanner
from app.schemas.api import AnalysisRunRequest
from app.schemas.common import AnalysisStatus, RiskLevel
from app.schemas.engine import (
    ContradictionResult,
    EligibilityResult,
    ReadinessResult,
    RiskResult,
)
from app.schemas.profile import BuiltProfile


@pytest.mark.asyncio
async def test_expected_mock_actions(pipeline, mock_cases) -> None:
    for case in mock_cases:
        result = (await pipeline.run(AnalysisRunRequest(**case))).action_plan
        assert [action.action_id for action in result.actions] == case[
            "expected_action_ids"
        ]


@pytest.mark.asyncio
async def test_pmjay_never_generates_actions(pipeline, mock_cases) -> None:
    case = next(case for case in mock_cases if case["program_id"] == "ayushman-bharat-pm-jay")
    assert (await pipeline.run(AnalysisRunRequest(**case))).action_plan.actions == []


def test_ready_application_gets_submit_action() -> None:
    planner = ActionPlanner()
    eligibility = EligibilityResult(
        program_id="verified-program",
        eligible=True,
        status=AnalysisStatus.ELIGIBLE,
    )
    readiness = ReadinessResult(
        readiness_score=100,
        risk_level=RiskLevel.LOW,
    )
    risk = RiskResult(
        risk_level=RiskLevel.LOW,
        explanation="No configured submission risk signals were detected.",
    )
    result = planner.plan(
        "verified-program",
        BuiltProfile(),
        eligibility,
        ContradictionResult(),
        readiness,
        risk,
    )
    assert [action.action_id for action in result.actions] == ["submit_application"]
