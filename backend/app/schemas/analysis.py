from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import AnalysisStatus, RiskLevel, RiskReason, TimestampedRead
from app.schemas.profile import FollowUpQuestion


class OfficialReference(BaseModel):
    text: str
    source_url: str
    section_reference: str
    score: float = Field(ge=0, le=1)


class AnalysisIssue(BaseModel):
    code: str
    category: str
    severity: RiskLevel
    message: str
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    official_reference: OfficialReference | None = None


class PlannedAction(BaseModel):
    priority: int = Field(ge=1)
    action_id: str
    instruction: str
    reason: str


class AnalysisResult(BaseModel):
    program: str
    status: AnalysisStatus
    eligible: bool | None
    readiness_score: float | None = Field(default=None, ge=0, le=100)
    risk_level: RiskLevel
    risk_reason: RiskReason | None = None
    issues: list[AnalysisIssue] = Field(default_factory=list)
    blockers: list[AnalysisIssue] = Field(default_factory=list)
    actions: list[PlannedAction] = Field(default_factory=list)
    questions: list[FollowUpQuestion] = Field(default_factory=list)
    explanations: list[str] = Field(default_factory=list)


class AnalysisCreate(BaseModel):
    citizen_profile_id: str
    program_id: str
    eligible: bool | None = None
    readiness_score: float | None = Field(default=None, ge=0, le=100)
    risk_level: RiskLevel | None = None
    result: dict[str, Any] = Field(default_factory=dict)


class AnalysisRead(TimestampedRead, AnalysisCreate):
    pass
