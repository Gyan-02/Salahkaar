import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.config.paths import DATA_PATH
from app.schemas.profile import (
    BuiltProfile,
    ProfileConflict,
    ProfileDocument,
    ProfileField,
    ProvenanceValue,
)
from app.schemas.program import DocumentSchemasConfiguration


class ProfileBuilderError(RuntimeError):
    pass


class ProfileBuilder:
    """Combines extracted fields while preserving every source and conflict."""

    def __init__(self, schema_path: Path | None = None) -> None:
        path = schema_path or DATA_PATH / "document_schemas.json"
        try:
            self.configuration = DocumentSchemasConfiguration.model_validate_json(
                path.read_text(encoding="utf-8")
            )
        except (FileNotFoundError, ValidationError) as exc:
            raise ProfileBuilderError(f"Invalid document schema configuration: {exc}") from exc

    def build(
        self,
        documents: list[ProfileDocument],
        required_fields: list[str] | None = None,
    ) -> BuiltProfile:
        collected: dict[str, list[ProvenanceValue]] = {}
        document_ids: list[str] = []

        for document in documents:
            definition = self.configuration.document_types.get(document.document_type)
            if definition is None:
                raise ProfileBuilderError(
                    f"Unsupported document type in profile: {document.document_type}"
                )
            if document.document_id:
                document_ids.append(document.document_id)
            for source_field, value in document.fields.items():
                if self._is_missing(value):
                    continue
                field_definition = definition.fields.get(source_field)
                if field_definition is None:
                    raise ProfileBuilderError(
                        f"Field {source_field!r} is not configured for {document.document_type}"
                    )
                profile_field = field_definition.profile_field or source_field
                collected.setdefault(profile_field, []).append(
                    ProvenanceValue(
                        value=value,
                        source=document.document_type,
                        document_id=document.document_id,
                    )
                )

        fields: dict[str, ProfileField] = {}
        conflicts: list[ProfileConflict] = []
        for field_name, values in collected.items():
            distinct = {self._comparison_key(item.value) for item in values}
            if len(distinct) > 1:
                conflict = ProfileConflict(field=field_name, values=values)
                conflicts.append(conflict)
                fields[field_name] = ProfileField(
                    conflicted=True,
                    values=values,
                )
            else:
                first = values[0]
                fields[field_name] = ProfileField(
                    value=first.value,
                    source=first.source,
                    document_id=first.document_id,
                    values=values,
                )

        required = list(dict.fromkeys(required_fields or []))
        missing = [field for field in required if field not in fields]
        return BuiltProfile(
            fields=fields,
            conflicts=conflicts,
            missing_fields=missing,
            document_ids=list(dict.fromkeys(document_ids)),
        )

    @staticmethod
    def _is_missing(value: Any) -> bool:
        return value is None or (isinstance(value, str) and not value.strip())

    @staticmethod
    def _comparison_key(value: Any) -> str:
        normalized = " ".join(value.split()).casefold() if isinstance(value, str) else value
        return json.dumps(normalized, sort_keys=True, default=str, ensure_ascii=False)
