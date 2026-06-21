from pathlib import Path

import chromadb

from app.config.settings import get_settings
from app.rag.embeddings import DeterministicHashEmbedder, normalize_tokens
from app.rag.ingestion import COLLECTION_NAME, CorpusIngestor
from app.rag.models import (
    GuidelineLookupResponse,
    ProgramId,
    RetrievedChunk,
    RetrievalStatus,
)


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "for", "from", "how",
    "i", "in", "is", "it", "me", "of", "on", "or", "the", "to", "what",
    "which", "who", "with", "under", "scheme", "program", "pm", "kisan",
    "pmjay", "jay", "ayushman", "bharat", "nmmss",
}


class GuidelineRetriever:
    def __init__(
        self,
        persist_path: Path | None = None,
        min_relevance: float | None = None,
        embedder: DeterministicHashEmbedder | None = None,
        auto_ingest: bool = True,
    ) -> None:
        settings = get_settings()
        self.persist_path = persist_path or settings.chroma_path
        self.min_relevance = (
            settings.rag_min_relevance if min_relevance is None else min_relevance
        )
        self.embedder = embedder or DeterministicHashEmbedder()
        self.client = chromadb.PersistentClient(path=str(self.persist_path))
        try:
            self.collection = self.client.get_collection(COLLECTION_NAME)
        except Exception:
            if not auto_ingest:
                raise
            CorpusIngestor(self.persist_path, self.embedder).ingest()
            self.collection = self.client.get_collection(COLLECTION_NAME)

    def retrieve(
        self,
        program: ProgramId,
        query: str,
        top_n: int = 3,
    ) -> GuidelineLookupResponse:
        content_terms = set(normalize_tokens(query)) - STOPWORDS
        if not content_terms:
            return self._no_match()
        candidate_count = max(top_n * 5, 10)
        raw = self.collection.query(
            query_embeddings=self.embedder.embed([query]),
            where={"program": program},
            n_results=candidate_count,
            include=["documents", "metadatas", "distances"],
        )
        ids = (raw.get("ids") or [[]])[0]
        documents = (raw.get("documents") or [[]])[0]
        metadatas = (raw.get("metadatas") or [[]])[0]
        distances = (raw.get("distances") or [[]])[0]
        hits: list[RetrievedChunk] = []
        for chunk_id, document, metadata, distance in zip(
            ids, documents, metadatas, distances, strict=True
        ):
            if document is None or metadata is None or distance is None:
                continue
            searchable = f"{metadata['section_reference']} {document}"
            chunk_terms = set(normalize_tokens(searchable)) - STOPWORDS
            overlap = content_terms & chunk_terms
            if not overlap:
                continue
            lexical_coverage = len(overlap) / len(content_terms)
            cosine_similarity = max(0.0, min(1.0, 1.0 - float(distance)))
            score = 0.55 * cosine_similarity + 0.45 * lexical_coverage
            if score < self.min_relevance:
                continue
            hits.append(
                RetrievedChunk(
                    id=chunk_id,
                    text=document,
                    score=round(score, 6),
                    program=metadata["program"],
                    source_url=metadata["source_url"],
                    section_reference=metadata["section_reference"],
                    retrieval_date=metadata["retrieval_date"],
                    source_status=metadata["source_status"],
                )
            )
        hits.sort(key=lambda item: item.score, reverse=True)
        selected = hits[:top_n]
        if not selected:
            return self._no_match()
        return GuidelineLookupResponse(result=selected, status=RetrievalStatus.MATCH)

    def close(self) -> None:
        self.client.close()

    @staticmethod
    def _no_match() -> GuidelineLookupResponse:
        return GuidelineLookupResponse(
            result=None,
            status=RetrievalStatus.NO_OFFICIAL_SOURCE_MATCH,
        )
