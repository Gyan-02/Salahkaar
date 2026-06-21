from functools import lru_cache

from app.api.pipeline import AnalysisPipeline
from app.engines.explanation_engine import ExplanationEngine
from app.rag.evidence import RagOfficialReferenceResolver
from app.rag.router import get_guideline_retriever


@lru_cache
def get_grounded_analysis_pipeline() -> AnalysisPipeline:
    resolver = RagOfficialReferenceResolver(get_guideline_retriever())
    return AnalysisPipeline(explanation_engine=ExplanationEngine(resolver))
