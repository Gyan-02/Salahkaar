from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


ProgramId = Literal["pm-kisan", "nmmss", "ayushman-bharat-pm-jay"]


class GuidelineChunk(BaseModel):
    id: str
    program: ProgramId
    source_url: HttpUrl
    section_reference: str
    retrieval_date: str
    source_status: str
    text: str = Field(min_length=1)


class LockedCorpus(BaseModel):
    schema_version: str
    locked: Literal[True]
    chunks: list[GuidelineChunk]


class RetrievalStatus(StrEnum):
    MATCH = "MATCH"
    NO_OFFICIAL_SOURCE_MATCH = "NO_OFFICIAL_SOURCE_MATCH"


class RetrievedChunk(BaseModel):
    id: str
    text: str
    score: float = Field(ge=0, le=1)
    program: ProgramId
    source_url: str
    section_reference: str
    retrieval_date: str
    source_status: str


class GuidelineLookupRequest(BaseModel):
    program: ProgramId
    query: str = Field(min_length=3, max_length=500)
    top_n: int = Field(default=3, ge=1, le=10)


class GuidelineLookupResponse(BaseModel):
    result: list[RetrievedChunk] | None
    status: RetrievalStatus


class IngestionResult(BaseModel):
    collection: str
    chunks_ingested: int
    corpus_schema_version: str

