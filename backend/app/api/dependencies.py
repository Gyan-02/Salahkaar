from functools import lru_cache

from app.api.pipeline import AnalysisPipeline


@lru_cache
def get_analysis_pipeline() -> AnalysisPipeline:
    return AnalysisPipeline()

