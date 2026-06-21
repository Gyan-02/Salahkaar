import json
from pathlib import Path

from app.rag.corpus import load_locked_corpus
from app.rag.ingestion import COLLECTION_NAME, CorpusIngestor


def test_locked_corpus_contains_only_approved_programs_and_sources() -> None:
    corpus = load_locked_corpus()
    assert corpus.locked is True
    assert len(corpus.chunks) == 34
    assert {chunk.program for chunk in corpus.chunks} == {
        "pm-kisan",
        "nmmss",
        "ayushman-bharat-pm-jay",
    }
    allowed_urls = {
        "https://pmkisan.gov.in/",
        "https://pmkisan.gov.in/Documents/RevisedPM-KISANOperationalGuidelines(English).pdf",
        "https://dsel.education.gov.in/sites/default/files/NMMSS_Guidelines_22.pdf",
        "https://nha.gov.in/PM-JAY",
    }
    assert {str(chunk.source_url) for chunk in corpus.chunks} == allowed_urls
    assert all(chunk.retrieval_date == "2026-06-21" for chunk in corpus.chunks)
    assert all(chunk.section_reference for chunk in corpus.chunks)
    assert all(chunk.source_status for chunk in corpus.chunks)


def test_pmjay_gap_topics_are_not_inserted_as_fake_clauses() -> None:
    chunks = [
        chunk for chunk in load_locked_corpus().chunks
        if chunk.program == "ayushman-bharat-pm-jay"
    ]
    searchable = " ".join(chunk.text.casefold() for chunk in chunks)
    assert "exclusion list" not in searchable
    assert "document checklist" not in searchable
    assert "required documents" not in searchable


def test_ingestion_is_idempotent_and_preserves_exact_text(tmp_path) -> None:
    corpus = load_locked_corpus()
    ingestor = CorpusIngestor(tmp_path / "chroma")
    try:
        first = ingestor.ingest()
        second = ingestor.ingest()
        collection = ingestor.client.get_collection(COLLECTION_NAME)
        assert first.chunks_ingested == len(corpus.chunks)
        assert second.chunks_ingested == len(corpus.chunks)
        assert collection.count() == len(corpus.chunks)
        stored = collection.get(ids=["nmmss-illness-01"], include=["documents", "metadatas"])
        source = next(chunk for chunk in corpus.chunks if chunk.id == "nmmss-illness-01")
        assert stored["documents"] == [source.text]
        assert stored["metadatas"][0]["source_url"] == str(source.source_url)
        assert stored["metadatas"][0]["section_reference"] == source.section_reference
        assert stored["metadatas"][0]["retrieval_date"] == source.retrieval_date
    finally:
        ingestor.close()


def test_source_audit_program_urls_cover_corpus() -> None:
    data_path = Path(__file__).parents[1] / "app" / "data"
    audit = json.loads((data_path / "source_audit.json").read_text(encoding="utf-8"))
    audit_urls = {source.get("url") for source in audit["sources"] if source.get("url")}
    corpus_urls = {str(chunk.source_url) for chunk in load_locked_corpus().chunks}
    assert corpus_urls <= audit_urls

