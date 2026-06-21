from fastapi.testclient import TestClient

from app.rag.ingestion import CorpusIngestor
from app.main import app
from app.rag.retriever import GuidelineRetriever
from app.rag.router import get_guideline_retriever


def test_grounded_lookup_endpoint_and_refusal_contract(tmp_path) -> None:
    original_overrides = dict(app.dependency_overrides)
    path = tmp_path / "chroma"
    ingestor = CorpusIngestor(path)
    ingestor.ingest()
    ingestor.close()
    retriever = GuidelineRetriever(path, min_relevance=0.35, auto_ingest=False)
    app.dependency_overrides[get_guideline_retriever] = lambda: retriever
    try:
        with TestClient(app) as client:
            match = client.post(
                "/guidelines/lookup",
                json={
                    "program": "nmmss",
                    "query": "What is the parental income limit?",
                    "top_n": 3,
                },
            )
            assert match.status_code == 200
            payload = match.json()
            assert payload["status"] == "MATCH"
            assert payload["result"][0]["id"] == "nmmss-eligibility-01"
            assert set(payload["result"][0]) == {
                "id", "text", "score", "program", "source_url",
                "section_reference", "retrieval_date", "source_status",
            }

            no_match = client.post(
                "/guidelines/lookup",
                json={
                    "program": "ayushman-bharat-pm-jay",
                    "query": "Which documents are required?",
                },
            )
            assert no_match.json() == {
                "result": None,
                "status": "NO_OFFICIAL_SOURCE_MATCH",
            }
            assert "/guidelines/lookup" in client.get("/openapi.json").json()["paths"]
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)
        retriever.close()
