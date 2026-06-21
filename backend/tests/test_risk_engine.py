import pytest

from app.engines.risk_engine import RiskEngine
from app.schemas.analysis import AnalysisIssue
from app.schemas.api import AnalysisRunRequest
from app.schemas.common import AnalysisStatus, RiskLevel, RiskReason
from app.schemas.engine import (
    ContradictionResult,
    EligibilityResult,
    FailedRule,
    ReadinessResult,
)
from app.schemas.profile import BuiltProfile


@pytest.mark.asyncio
async def test_contradiction_and_incomplete_rules_produce_high_risk(
    pipeline, mock_cases
) -> None:
    case = next(case for case in mock_cases if case["program_id"] == "pm-kisan")
    result = (await pipeline.run(AnalysisRunRequest(**case))).risk
    assert result.risk_level == RiskLevel.HIGH
    assert result.risk_reason == RiskReason.MULTIPLE_FACTORS
    assert {signal.code for signal in result.signals} >= {
        "official_source_required",
        "cross_document_name_mismatch",
    }


@pytest.mark.asyncio
async def test_pmjay_risk_is_not_computed(pipeline, mock_cases) -> None:
    case = next(case for case in mock_cases if case["program_id"] == "ayushman-bharat-pm-jay")
    result = (await pipeline.run(AnalysisRunRequest(**case))).risk
    assert result.risk_level == RiskLevel.PENDING
    assert result.risk_reason == RiskReason.POLICY_INCOMPLETE
    assert result.signals == []
    assert "not computed" in result.explanation


@pytest.mark.asyncio
async def test_low_quality_adds_medium_signal(pipeline, mock_cases) -> None:
    case = next(case for case in mock_cases if case["program_id"] == "pm-kisan")
    request = AnalysisRunRequest(**case, document_quality=["LOW"])
    result = (await pipeline.run(request)).risk
    signal = next(signal for signal in result.signals if signal.code == "low_document_quality")
    assert signal.level == RiskLevel.MEDIUM


@pytest.mark.asyncio
async def test_clean_partial_policy_has_policy_incomplete_reason(
    pipeline, mock_cases
) -> None:
    case = next(case for case in mock_cases if case["id"] == "pm-kisan-clean-readiness")
    result = (await pipeline.run(AnalysisRunRequest(**case))).risk
    assert result.risk_reason == RiskReason.POLICY_INCOMPLETE


def test_multiple_document_issues_are_one_risk_category() -> None:
    issues = [
        AnalysisIssue(
            code="name_mismatch",
            category="contradiction",
            severity=RiskLevel.HIGH,
            message="Name mismatch",
        ),
        AnalysisIssue(
            code="expired_document",
            category="contradiction",
            severity=RiskLevel.HIGH,
            message="Expired document",
        ),
    ]
    eligibility = EligibilityResult(
        program_id="complete-program",
        eligible=True,
        status=AnalysisStatus.ELIGIBLE,
        official_source_required=False,
    )
    result = RiskEngine().assess(
        BuiltProfile(),
        eligibility,
        ContradictionResult(issues=issues),
        ReadinessResult(
            readiness_score=50,
            risk_level=RiskLevel.MEDIUM,
            blockers=issues,
        ),
    )
    assert result.risk_reason == RiskReason.DOCUMENT_BLOCKERS


def test_policy_and_document_categories_become_multiple_factors() -> None:
    issue = AnalysisIssue(
        code="name_mismatch",
        category="contradiction",
        severity=RiskLevel.HIGH,
        message="Name mismatch",
    )
    eligibility = EligibilityResult(
        program_id="partial-program",
        eligible=None,
        status=AnalysisStatus.PARTIAL_RULES_EVALUATED,
        official_source_required=True,
    )
    result = RiskEngine().assess(
        BuiltProfile(),
        eligibility,
        ContradictionResult(issues=[issue]),
        ReadinessResult(
            readiness_score=75,
            risk_level=RiskLevel.MEDIUM,
            blockers=[issue],
        ),
    )
    assert result.risk_reason == RiskReason.MULTIPLE_FACTORS


def test_verified_rule_failure_has_eligibility_failure_reason() -> None:
    failed_rule = FailedRule(
        rule_id="income_limit",
        field="income",
        operator="<=",
        expected_value=100,
        actual_value=101,
        description="Income exceeds the verified limit.",
    )
    eligibility = EligibilityResult(
        program_id="complete-program",
        eligible=False,
        status=AnalysisStatus.INELIGIBLE,
        failed_rules=[failed_rule],
        official_source_required=False,
    )
    result = RiskEngine().assess(
        BuiltProfile(),
        eligibility,
        ContradictionResult(),
        ReadinessResult(readiness_score=70, risk_level=RiskLevel.MEDIUM),
    )
    assert result.risk_reason == RiskReason.ELIGIBILITY_FAILURE


def test_no_risk_factors_has_null_reason() -> None:
    eligibility = EligibilityResult(
        program_id="complete-program",
        eligible=True,
        status=AnalysisStatus.ELIGIBLE,
        official_source_required=False,
    )
    result = RiskEngine().assess(
        BuiltProfile(),
        eligibility,
        ContradictionResult(),
        ReadinessResult(readiness_score=100, risk_level=RiskLevel.LOW),
    )
    assert result.risk_level == RiskLevel.LOW
    assert result.risk_reason is None
