import pytest

from app.rag.corpus import load_locked_corpus
from app.rag.ingestion import CorpusIngestor
from app.rag.models import RetrievalStatus
from app.rag.retriever import GuidelineRetriever


@pytest.fixture
def retriever(tmp_path):
    path = tmp_path / "chroma"
    ingestor = CorpusIngestor(path)
    ingestor.ingest()
    ingestor.close()
    service = GuidelineRetriever(path, min_relevance=0.35, auto_ingest=False)
    try:
        yield service
    finally:
        service.close()


@pytest.mark.parametrize(
    ("program", "query", "expected_first"),
    [
        ("pm-kisan", "Who paid income tax in the last assessment year?", "pmkisan-exclusion-05"),
        ("pm-kisan", "What is the land ownership cutoff date?", "pmkisan-cutoff-01"),
        ("nmmss", "What is the parental income limit?", "nmmss-eligibility-01"),
        ("nmmss", "What are the MAT SAT pass marks?", "nmmss-test-cutoff-01"),
        ("ayushman-bharat-pm-jay", "Is treatment portable across India?", "pmjay-portability-01"),
    ],
)
def test_strong_queries_return_expected_official_chunk(
    retriever, program, query, expected_first
) -> None:
    response = retriever.retrieve(program, query)
    assert response.status == RetrievalStatus.MATCH
    assert response.result
    assert response.result[0].id == expected_first


def test_results_preserve_score_order_and_exact_source_text(retriever) -> None:
    response = retriever.retrieve(
        "pm-kisan",
        "government employees pensioners and income tax exclusions",
        top_n=3,
    )
    assert response.result
    scores = [chunk.score for chunk in response.result]
    assert scores == sorted(scores, reverse=True)
    assert len(response.result) <= 3
    source_by_id = {chunk.id: chunk for chunk in load_locked_corpus().chunks}
    for hit in response.result:
        assert hit.text == source_by_id[hit.id].text
        assert hit.source_url == str(source_by_id[hit.id].source_url)
        assert hit.section_reference == source_by_id[hit.id].section_reference


@pytest.mark.parametrize(
    "query",
    [
        "What are the PM-JAY exclusion categories?",
        "Which documents are required for PM-JAY?",
        "Give me the PM-JAY document checklist",
        "Are government employees excluded from PM-JAY?",
    ],
)
def test_pmjay_policy_gaps_return_explicit_no_match(retriever, query) -> None:
    response = retriever.retrieve("ayushman-bharat-pm-jay", query)
    assert response.model_dump(mode="json") == {
        "result": None,
        "status": "NO_OFFICIAL_SOURCE_MATCH",
    }


def test_unrelated_query_does_not_get_low_relevance_chunk(retriever) -> None:
    response = retriever.retrieve("nmmss", "weather forecast and railway timetable")
    assert response.result is None
    assert response.status == RetrievalStatus.NO_OFFICIAL_SOURCE_MATCH


def test_program_filter_prevents_cross_program_results(retriever) -> None:
    response = retriever.retrieve("nmmss", "PM-KISAN income tax exclusion")
    assert response.result is None or all(
        chunk.program == "nmmss" for chunk in response.result
    )


def test_top_n_is_respected(retriever) -> None:
    response = retriever.retrieve(
        "pm-kisan",
        "land ownership cutoff and inheritance",
        top_n=2,
    )
    assert response.result is not None
    assert len(response.result) == 2
