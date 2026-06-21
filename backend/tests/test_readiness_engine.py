from copy import deepcopy

import pytest

from app.schemas.api import AnalysisRunRequest
from app.schemas.common import RiskLevel


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("program_id", "expected_score"),
    [("pm-kisan", 75.0), ("nmmss", 50.0)],
)
async def test_mock_readiness_scores(
    pipeline, mock_cases, program_id, expected_score
) -> None:
    case = next(case for case in mock_cases if case["program_id"] == program_id)
    result = (await pipeline.run(AnalysisRunRequest(**case))).readiness
    assert result.readiness_score == expected_score
    assert result.blockers


@pytest.mark.asyncio
async def test_missing_required_answer_reduces_score(pipeline, mock_cases) -> None:
    case = deepcopy(next(case for case in mock_cases if case["program_id"] == "pm-kisan"))
    del case["answers"]["institutional_landholder"]
    result = (await pipeline.run(AnalysisRunRequest(**case))).readiness
    assert result.readiness_score == 60.0
    assert {rule.rule_id for rule in result.applied_rules} == {
        "high_severity_contradiction",
        "missing_required_information",
    }


@pytest.mark.asyncio
async def test_low_document_quality_reduces_score(pipeline, mock_cases) -> None:
    case = deepcopy(next(case for case in mock_cases if case["program_id"] == "pm-kisan"))
    case["document_quality"] = ["LOW"]
    result = (await pipeline.run(AnalysisRunRequest(**case))).readiness
    assert result.readiness_score == 65.0
    assert "low_document_quality" in {rule.rule_id for rule in result.applied_rules}


@pytest.mark.asyncio
async def test_pmjay_readiness_is_not_computed(pipeline, mock_cases) -> None:
    case = next(case for case in mock_cases if case["program_id"] == "ayushman-bharat-pm-jay")
    result = (await pipeline.run(AnalysisRunRequest(**case))).readiness
    assert result.readiness_score is None
    assert result.risk_level == RiskLevel.PENDING
    assert result.blockers == []
    assert result.applied_rules == []

