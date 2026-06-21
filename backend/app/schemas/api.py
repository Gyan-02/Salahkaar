from typing import Any

from pydantic import BaseModel, Field

from app.schemas.analysis import AnalysisResult
from app.schemas.document import DocumentRead, ExtractionResult
from app.schemas.profile import FollowUpQuestion, ProfileDocument


class MockDocumentPayload(BaseModel):
    document_type: str
    fields: dict[str, Any]
    filename: str | None = None
    document_id: str | None = None


class AnalysisRunRequest(BaseModel):
    program_id: str
    documents: list[MockDocumentPayload] = Field(min_length=1)
    answers: dict[str, Any] = Field(default_factory=dict)
    document_quality: list[str] = Field(default_factory=list)


class DocumentsCheckRequest(BaseModel):
    documents: list[ProfileDocument] = Field(min_length=1)


class UploadResponse(BaseModel):
    upload_token: str
    filename: str
    content_type: str


class ExtractUploadRequest(BaseModel):
    upload_token: str
    document_type: str
    mock_fields: dict[str, Any] | None = None
    consent_to_external_processing: bool = False


class ExtractUploadResponse(BaseModel):
    extraction: ExtractionResult
    document: DocumentRead


class QuestionsResponse(BaseModel):
    questions: list[FollowUpQuestion] = Field(default_factory=list)


class DemoCaseResponse(AnalysisResult):
    case_id: str
