from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ExtractionStatus, TimestampedRead


class ExtractionInput(BaseModel):
    filename: str
    content_type: str
    content: bytes = Field(repr=False)
    document_type: str | None = None
    mock_fields: dict[str, Any] | None = None


class ExtractionResult(BaseModel):
    document_type: str
    fields: dict[str, Any]
    extractor: str
    status: ExtractionStatus
    fallback_used: bool = False
    failure_reason: str | None = None


class DocumentCreate(BaseModel):
    document_type: str
    original_filename: str
    content_type: str
    extracted_fields: dict[str, Any]
    extractor: str
    extraction_status: str
    extraction_failure_reason: str | None = None


class DocumentRead(TimestampedRead, DocumentCreate):
    pass

