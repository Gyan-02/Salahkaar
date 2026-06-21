from datetime import date

import pytest

from app.engines.contradiction_engine import ContradictionEngine
from app.schemas.api import AnalysisRunRequest
from app.schemas.profile import ProfileDocument


@pytest.mark.asyncio
async def test_configured_mock_contradictions(pipeline, mock_cases) -> None:
    for case in mock_cases:
        execution = await pipeline.run(AnalysisRunRequest(**case))
        assert [issue.code for issue in execution.contradictions.issues] == case[
            "expected_contradiction_ids"
        ]


def test_specific_bank_mismatch_suppresses_generic_duplicate(profile_builder) -> None:
    profile = profile_builder.build(
        [
            ProfileDocument(document_type="aadhaar", fields={"name": "Asha Devi"}),
            ProfileDocument(document_type="bank_passbook", fields={"name": "Asha Davi"}),
        ]
    )
    result = ContradictionEngine(today=date(2026, 6, 21)).check(profile)
    assert [issue.code for issue in result.issues] == ["bank_account_holder_mismatch"]


def test_expiry_date_equal_to_today_is_not_expired(profile_builder) -> None:
    profile = profile_builder.build(
        [
            ProfileDocument(
                document_type="income_certificate",
                fields={"expiry_date": "2026-06-21"},
            )
        ]
    )
    result = ContradictionEngine(today=date(2026, 6, 21)).check(profile)
    assert result.issues == []


def test_address_mismatch_has_medium_severity(profile_builder) -> None:
    profile = profile_builder.build(
        [
            ProfileDocument(document_type="aadhaar", fields={"address": "Patna"}),
            ProfileDocument(document_type="bank_passbook", fields={"address": "Chennai"}),
        ]
    )
    result = ContradictionEngine(today=date(2026, 6, 21)).check(profile)
    assert result.issues[0].code == "cross_document_address_mismatch"
    assert result.issues[0].severity.value == "MEDIUM"

