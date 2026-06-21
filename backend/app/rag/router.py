from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends

from app.rag.models import GuidelineLookupRequest, GuidelineLookupResponse
from app.rag.retriever import GuidelineRetriever


router = APIRouter(prefix="/guidelines", tags=["official-guidelines"])


@lru_cache
def get_guideline_retriever() -> GuidelineRetriever:
    return GuidelineRetriever()


RetrieverDependency = Annotated[
    GuidelineRetriever, Depends(get_guideline_retriever)
]


@router.post("/lookup", response_model=GuidelineLookupResponse)
def lookup_guidelines(
    request: GuidelineLookupRequest,
    retriever: RetrieverDependency,
) -> GuidelineLookupResponse:
    return retriever.retrieve(
        program=request.program,
        query=request.query,
        top_n=request.top_n,
    )

