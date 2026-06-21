from pathlib import Path

from pydantic import ValidationError

from app.config.paths import DATA_PATH
from app.rag.models import LockedCorpus


class CorpusError(RuntimeError):
    pass


def load_locked_corpus(path: Path | None = None) -> LockedCorpus:
    corpus_path = path or DATA_PATH / "rag_corpus.json"
    try:
        corpus = LockedCorpus.model_validate_json(corpus_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValidationError) as exc:
        raise CorpusError(f"Invalid locked RAG corpus: {exc}") from exc
    ids = [chunk.id for chunk in corpus.chunks]
    if len(ids) != len(set(ids)):
        raise CorpusError("Locked RAG corpus contains duplicate chunk ids")
    if not corpus.chunks:
        raise CorpusError("Locked RAG corpus is empty")
    return corpus

