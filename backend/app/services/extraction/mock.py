import json
from pathlib import Path
from typing import Any

from app.config.paths import DATA_PATH
from app.schemas.common import ExtractionStatus
from app.schemas.document import ExtractionInput, ExtractionResult
from app.services.extraction.base import DocumentExtractor, ExtractionError


class MockExtractor(DocumentExtractor):
    """Deterministic extractor for demos and tests; it never performs OCR."""

    def __init__(self, schema_path: Path | None = None) -> None:
        path = schema_path or DATA_PATH / "document_schemas.json"
        with path.open(encoding="utf-8") as handle:
            self.schemas: dict[str, Any] = json.load(handle)["document_types"]

    async def extract(self, document: ExtractionInput) -> ExtractionResult:
        document_type, fields = self._payload(document)
        if document_type not in self.schemas:
            raise ExtractionError(f"Unsupported mock document type: {document_type}")

        allowed = list(self.schemas[document_type]["fields"])
        unknown = set(fields) - set(allowed)
        if unknown:
            raise ExtractionError(
                f"Mock fields are not in the {document_type} schema: {sorted(unknown)}"
            )

        normalized = {field: fields.get(field) for field in allowed}
        return ExtractionResult(
            document_type=document_type,
            fields=normalized,
            extractor="mock",
            status=ExtractionStatus.SUCCEEDED,
        )

    def _payload(self, document: ExtractionInput) -> tuple[str, dict[str, Any]]:
        if document.mock_fields is not None:
            if not document.document_type:
                raise ExtractionError("document_type is required with mock_fields")
            return document.document_type, document.mock_fields

        if document.content_type == "application/json":
            try:
                payload = json.loads(document.content.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ExtractionError("Invalid JSON mock document") from exc
            document_type = document.document_type or payload.get("document_type")
            fields = payload.get("fields", {})
            if not document_type or not isinstance(fields, dict):
                raise ExtractionError("Mock JSON needs document_type and object fields")
            return document_type, fields

        if not document.document_type:
            raise ExtractionError("document_type is required for a non-JSON mock document")
        raise ExtractionError(
            "Mock extraction needs mock_fields or an application/json fixture; "
            "binary OCR is not enabled in this pass"
        )
