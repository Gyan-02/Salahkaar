import pytest

from app.schemas.api import AnalysisRunRequest


@pytest.mark.asyncio
async def test_pm_kisan_explanation_attributes_high_blocker_points(
    pipeline, mock_cases
) -> None:
    case = next(case for case in mock_cases if case["id"] == "pm-kisan-name-land-mismatch")
    explanations = (await pipeline.run(AnalysisRunRequest(**case))).result.explanations
    assert (
        "Score reduced by 25 points: 1 HIGH-severity contradiction — "
        "Names differ across supplied documents. Review the source documents before applying."
    ) in explanations
    assert "Final readiness score: 75/100 (MEDIUM)." in explanations


@pytest.mark.asyncio
async def test_nmmss_explanation_attributes_both_high_blockers(
    pipeline, mock_cases
) -> None:
    case = next(case for case in mock_cases if case["id"] == "nmmss-expired-income-bank-name")
    explanations = (await pipeline.run(AnalysisRunRequest(**case))).result.explanations
    assert (
        "Score reduced by 50 points: 2 HIGH-severity contradictions — "
        "The bank account holder name differs from the identity document name; "
        "A supplied document has expired."
    ) in explanations
    assert "Final readiness score: 50/100 (MEDIUM)." in explanations


@pytest.mark.asyncio
async def test_clean_case_explains_no_deductions(pipeline, mock_cases) -> None:
    case = next(case for case in mock_cases if case["id"] == "pm-kisan-clean-readiness")
    result = (await pipeline.run(AnalysisRunRequest(**case))).result
    assert result.readiness_score == 100
    assert result.blockers == []
    assert result.actions == []
    assert (
        "No readiness points were deducted: no configured document, information, eligibility, or quality blockers were detected."
    ) in result.explanations
    assert "Final readiness score: 100/100 (LOW)." in result.explanations


@pytest.mark.asyncio
async def test_pending_policy_does_not_explain_a_score(pipeline, mock_cases) -> None:
    case = next(case for case in mock_cases if case["id"] == "pm-jay-family-composition-mismatch")
    result = (await pipeline.run(AnalysisRunRequest(**case))).result
    assert "Readiness was not computed while official rules are pending." in result.explanations
    assert not any(line.startswith("Final readiness score") for line in result.explanations)

