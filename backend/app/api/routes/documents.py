from dataclasses import dataclass
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_analysis_pipeline
from app.api.pipeline import AnalysisPipeline
from app.config.database import get_db
from app.config.settings import get_settings
from app.repositories.unit_of_work import UnitOfWork
from app.schemas.api import ExtractUploadRequest, ExtractUploadResponse, UploadResponse
from app.schemas.document import DocumentCreate, DocumentRead, ExtractionInput
from app.services.extraction.base import ExtractionError
from app.services.extraction.gemini import GeminiExtractor


router = APIRouter(prefix="/documents", tags=["documents"])
PipelineDependency = Annotated[AnalysisPipeline, Depends(get_analysis_pipeline)]
SessionDependency = Annotated[Session, Depends(get_db)]


@dataclass(slots=True)
class PendingUpload:
    path: Path
    filename: str
    content_type: str


_uploads: dict[str, PendingUpload] = {}


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: Annotated[UploadFile, File(...)]) -> UploadResponse:
    settings = get_settings()
    allowed_types = GeminiExtractor.SUPPORTED_CONTENT_TYPES | {"application/json"}
    content_type = file.content_type or "application/octet-stream"
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload a PDF, JPEG, PNG, or WebP document.",
        )
    content = await file.read(settings.max_upload_bytes + 1)
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="The uploaded document is larger than the configured limit.",
        )
    token = str(uuid4())
    upload_root = settings.upload_path
    upload_root.mkdir(parents=True, exist_ok=True)
    path = upload_root / token
    path.write_bytes(content)
    filename = file.filename or "document"
    _uploads[token] = PendingUpload(path=path, filename=filename, content_type=content_type)
    return UploadResponse(upload_token=token, filename=filename, content_type=content_type)


@router.post("/extract", response_model=ExtractUploadResponse)
async def extract_document(
    request: ExtractUploadRequest,
    pipeline: PipelineDependency,
    session: SessionDependency,
) -> ExtractUploadResponse:
    pending = _uploads.pop(request.upload_token, None)
    if pending is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown upload token")
    try:
        if request.mock_fields is not None:
            extractor = pipeline.extractor
        else:
            settings = get_settings()
            if not request.consent_to_external_processing:
                raise ExtractionError(
                    "Consent is required before sending a document to Gemini."
                )
            if not settings.use_gemini_extractor:
                raise ExtractionError(
                    "# ENV_REQUIRED: set USE_GEMINI_EXTRACTOR=true for live extraction"
                )
            extractor = GeminiExtractor(settings=settings)
        extraction = await extractor.extract(
            ExtractionInput(
                filename=pending.filename,
                content_type=pending.content_type,
                content=pending.path.read_bytes(),
                document_type=request.document_type,
                mock_fields=request.mock_fields,
            )
        )
        with UnitOfWork(session) as unit:
            entity = unit.documents.create(
                DocumentCreate(
                    document_type=extraction.document_type,
                    original_filename=pending.filename,
                    content_type=pending.content_type,
                    extracted_fields=extraction.fields,
                    extractor=extraction.extractor,
                    extraction_status=extraction.status.value,
                    extraction_failure_reason=extraction.failure_reason,
                )
            )
        return ExtractUploadResponse(
            extraction=extraction,
            document=DocumentRead.model_validate(entity),
        )
    except ExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    finally:
        pending.path.unlink(missing_ok=True)
