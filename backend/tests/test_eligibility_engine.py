from copy import deepcopy

import pytest

from app.engines.eligibility_engine import EligibilityEngine, RuleEvaluationError
from app.schemas.api import AnalysisRunRequest
from app.schemas.common import AnalysisStatus
from app.schemas.program import EligibilityRule


@pytest.mark.asyncio
async def test_known_rules_pass_but_partial_program_remains_unknown(
    pipeline, mock_cases
) -> None:
    case = next(case for case in mock_cases if case["program_id"] == "pm-kisan")
    result = (await pipeline.run(AnalysisRunRequest(**case))).eligibility
    assert result.eligible is None
    assert result.status == AnalysisStatus.PARTIAL_RULES_EVALUATED
    assert result.failed_rules == []


@pytest.mark.asyncio
async def test_verified_pm_kisan_exclusion_can_fail(pipeline, mock_cases) -> None:
    case = deepcopy(next(case for case in mock_cases if case["program_id"] == "pm-kisan"))
    case["answers"]["paid_income_tax_last_assessment_year"] = True
    result = (await pipeline.run(AnalysisRunRequest(**case))).eligibility
    assert result.eligible is False
    assert result.status == AnalysisStatus.INELIGIBLE
    assert [rule.rule_id for rule in result.failed_rules] == ["pmkisan_no_recent_income_tax"]


@pytest.mark.asyncio
async def test_nmmss_income_boundary(pipeline, mock_cases) -> None:
    case = deepcopy(next(case for case in mock_cases if case["program_id"] == "nmmss"))
    case["answers"]["parental_annual_income"] = 350000
    boundary = (await pipeline.run(AnalysisRunRequest(**case))).eligibility
    assert not any(rule.rule_id == "nmmss_income_limit" for rule in boundary.failed_rules)
    case["answers"]["parental_annual_income"] = 350001
    failed = (await pipeline.run(AnalysisRunRequest(**case))).eligibility
    assert failed.eligible is False
    assert "nmmss_income_limit" in {rule.rule_id for rule in failed.failed_rules}


@pytest.mark.asyncio
async def test_missing_answer_generates_question(pipeline, mock_cases) -> None:
    case = deepcopy(next(case for case in mock_cases if case["program_id"] == "pm-kisan"))
    del case["answers"]["paid_income_tax_last_assessment_year"]
    result = (await pipeline.run(AnalysisRunRequest(**case))).eligibility
    assert result.status == AnalysisStatus.INFORMATION_REQUIRED
    assert result.missing_fields == ["paid_income_tax_last_assessment_year"]
    assert result.questions[0].field == "paid_income_tax_last_assessment_year"


@pytest.mark.asyncio
async def test_pmjay_is_hard_short_circuited(pipeline, mock_cases) -> None:
    case = next(case for case in mock_cases if case["program_id"] == "ayushman-bharat-pm-jay")
    result = (await pipeline.run(AnalysisRunRequest(**case))).eligibility
    assert result.model_dump(mode="json") == {
        "program_id": "ayushman-bharat-pm-jay",
        "eligible": None,
        "status": "OFFICIAL_RULES_PENDING",
        "failed_rules": [],
        "unevaluated_rules": [],
        "missing_fields": [],
        "questions": [],
        "official_source_required": True,
    }


@pytest.mark.parametrize(
    ("operator", "actual", "expected"),
    [
        ("==", "Yes", "yes"),
        ("!=", "yes", "no"),
        ("<", 4, 5),
        ("<=", 5, 5),
        (">", 6, 5),
        (">=", "2026-01-01", "2026-01-01"),
        ("contains", "Patna, Bihar", "bihar"),
    ],
)
def test_all_supported_operators(operator, actual, expected) -> None:
    rule = EligibilityRule(
        id="operator-test",
        field="value",
        operator=operator,
        value=expected,
        description="operator test",
        official_source="test",
    )
    assert EligibilityEngine._evaluate(rule, actual) is True


def test_ordered_operator_rejects_unordered_strings() -> None:
    rule = EligibilityRule(
        id="invalid-order",
        field="value",
        operator=">",
        value="beta",
        description="invalid",
        official_source="test",
    )
    with pytest.raises(RuleEvaluationError):
        EligibilityEngine._evaluate(rule, "alpha")
