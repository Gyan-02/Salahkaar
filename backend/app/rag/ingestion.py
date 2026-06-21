from pathlib import Path

import chromadb

from app.config.settings import get_settings
from app.rag.corpus import load_locked_corpus
from app.rag.embeddings import DeterministicHashEmbedder
from app.rag.models import IngestionResult


COLLECTION_NAME = "official_benefit_guidelines"


class CorpusIngestor:
    def __init__(
        self,
        persist_path: Path | None = None,
        embedder: DeterministicHashEmbedder | None = None,
    ) -> None:
        self.persist_path = persist_path or get_settings().chroma_path
        self.persist_path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.persist_path))
        self.embedder = embedder or DeterministicHashEmbedder()

    def ingest(self) -> IngestionResult:
        corpus = load_locked_corpus()
        try:
            self.client.delete_collection(COLLECTION_NAME)
        except Exception as exc:
            if "does not exist" not in str(exc).casefold() and "not found" not in str(exc).casefold():
                raise
        collection = self.client.get_or_create_collection(
            COLLECTION_NAME,
            metadata={"hnsw:space": "cosine", "corpus_schema_version": corpus.schema_version},
        )
        embedding_texts = [
            f"{chunk.section_reference} {chunk.text}" for chunk in corpus.chunks
        ]
        collection.upsert(
            ids=[chunk.id for chunk in corpus.chunks],
            documents=[chunk.text for chunk in corpus.chunks],
            embeddings=self.embedder.embed(embedding_texts),
            metadatas=[
                {
                    "program": chunk.program,
                    "source_url": str(chunk.source_url),
                    "section_reference": chunk.section_reference,
                    "retrieval_date": chunk.retrieval_date,
                    "source_status": chunk.source_status,
                }
                for chunk in corpus.chunks
            ],
        )
        return IngestionResult(
            collection=COLLECTION_NAME,
            chunks_ingested=len(corpus.chunks),
            corpus_schema_version=corpus.schema_version,
        )

    def close(self) -> None:
        self.client.close()


if __name__ == "__main__":
    print(CorpusIngestor().ingest().model_dump_json(indent=2))
