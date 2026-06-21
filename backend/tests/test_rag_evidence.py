from typing import Any

import pytest

from app.api.pipeline import AnalysisPipeline
from app.engines.explanation_engine import ExplanationEngine
from app.rag.evidence import ISSUE_RETRIEVAL_QUERIES, RagOfficialReferenceResolver
from app.rag.ingestion import CorpusIngestor
from app.rag.retriever import GuidelineRetriever
from app.schemas.api import AnalysisRunRequest


class FailingRetriever:
    def retrieve(self, **_: Any) -> None:
        raise AssertionError("retrieval must not be invoked")


def _retriever(tmp_path) -> GuidelineRetriever:
    path = tmp_path / "chroma"
    ingestor = CorpusIngestor(path)
    ingestor.ingest()
    ingestor.close()
    return GuidelineRetriever(path, min_relevance=0.35, auto_ingest=False)


def test_mapping_is_explicit_and_contains_required_queries() -> None:
    assert ISSUE_RETRIEVAL_QUERIES[("pm-kisan", "income_tax_exclusion")] == (
        "income tax exclusion"
    )
    assert ISSUE_RETRIEVAL_QUERIES[("nmmss", "parental_income_limit")] == (
        "parental income limit"
    )
    assert ISSUE_RETRIEVAL_QUERIES[("nmmss", "scholarship_continuation")] == (
        "continuation of scholarship"
    )
    assert ISSUE_RETRIEVAL_QUERIES[("nmmss", "expired_document")] == (
        "document validity"
    )
    assert ISSUE_RETRIEVAL_QUERIES[("nmmss", "bank_account_holder_mismatch")] == (
        "bank account"
    )


def test_unmapped_and_pmjay_issues_never_invoke_retrieval() -> None:
    resolver = RagOfficialReferenceResolver(FailingRetriever())  # type: ignore[arg-type]
    assert resolver("pm-kisan", "cross_document_name_mismatch") is None
    assert resolver("ayushman-bharat-pm-jay", "family_composition_mismatch") is None


def test_resolver_rejects_topical_bank_chunk_and_other_weak_matches(tmp_path) -> None:
    retriever = _retriever(tmp_path)
    try:
        resolver = RagOfficialReferenceResolver(retriever)
        bank = resolver("nmmss", "bank_account_holder_mismatch")
        assert bank is None
        income_tax = resolver("pm-kisan", "pmkisan_no_recent_income_tax")
        assert income_tax is not None
        assert income_tax.text == (
            "All Persons who paid Income Tax in last assessment year."
        )
        assert income_tax.score >= 0.35
        assert resolver("nmmss", "expired_document") is None
    finally:
        retriever.close()


@pytest.mark.asyncio
async def test_explanation_integration_is_additive_only(mock_cases, tmp_path) -> None:
    case = next(item for item in mock_cases if item["id"] == "nmmss-expired-income-bank-name")
    request = AnalysisRunRequest.model_validate(case)
    baseline = await AnalysisPipeline().run(request)
    retriever = _retriever(tmp_path)
    try:
        grounded = await AnalysisPipeline(
            ExplanationEngine(RagOfficialReferenceResolver(retriever))
        ).run(request)
    finally:
        retriever.close()

    assert grounded.result.explanations == baseline.result.explanations
    assert grounded.result.readiness_score == baseline.result.readiness_score
    assert grounded.result.risk_level == baseline.result.risk_level
    assert grounded.result.risk_reason == baseline.result.risk_reason
    assert grounded.result.eligible == baseline.result.eligible
    assert grounded.result.status == baseline.result.status

    by_code = {issue.code: issue for issue in grounded.result.issues}
    assert by_code["bank_account_holder_mismatch"].official_reference is None
    assert by_code["expired_document"].official_reference is None
    blocker_by_code = {issue.code: issue for issue in grounded.result.blockers}
    assert blocker_by_code["bank_account_holder_mismatch"].official_reference is None
    assert blocker_by_code["expired_document"].official_reference is None


@pytest.mark.asyncio
async def test_pmjay_pipeline_never_retrieves_and_returns_null_reference(mock_cases) -> None:
    case = next(
        item for item in mock_cases
        if item["id"] == "pm-jay-family-composition-mismatch"
    )
    resolver = RagOfficialReferenceResolver(FailingRetriever())  # type: ignore[arg-type]
    execution = await AnalysisPipeline(ExplanationEngine(resolver)).run(
        AnalysisRunRequest.model_validate(case)
    )
    assert execution.result.status.value == "OFFICIAL_RULES_PENDING"
    assert execution.result.risk_level.value == "PENDING"
    assert execution.result.risk_reason.value == "POLICY_INCOMPLETE"
    assert execution.result.issues[0].official_reference is None


def test_analysis_endpoint_rejects_topical_but_unsupported_blocker(
    api_client, mock_cases
) -> None:
    client, _ = api_client
    case = next(item for item in mock_cases if item["id"] == "nmmss-expired-income-bank-name")
    response = client.post("/analysis/run", json=case)
    assert response.status_code == 200
    payload = response.json()
    bank = next(
        issue for issue in payload["blockers"]
        if issue["code"] == "bank_account_holder_mismatch"
    )
    assert bank["official_reference"] is None
