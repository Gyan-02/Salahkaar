from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedRead


class ProvenanceValue(BaseModel):
    value: Any
    source: str
    document_id: str | None = None


class ProfileField(BaseModel):
    value: Any | None = None
    source: str | None = None
    document_id: str | None = None
    conflicted: bool = False
    values: list[ProvenanceValue] = Field(default_factory=list)


class ProfileConflict(BaseModel):
    field: str
    conflicted: bool = True
    values: list[ProvenanceValue]


class CitizenProfileCreate(BaseModel):
    fields: dict[str, Any]
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    document_ids: list[str] = Field(default_factory=list)


class CitizenProfileRead(TimestampedRead, CitizenProfileCreate):
    pass


class FollowUpQuestion(BaseModel):
    field: str
    question: str
    required_for_program: str | None = None


class ProfileDocument(BaseModel):
    document_type: str
    fields: dict[str, Any]
    document_id: str | None = None


class BuiltProfile(BaseModel):
    fields: dict[str, ProfileField] = Field(default_factory=dict)
    conflicts: list[ProfileConflict] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    document_ids: list[str] = Field(default_factory=list)
