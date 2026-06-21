from typing import Any

from pydantic import BaseModel, Field

from app.schemas.analysis import AnalysisIssue, PlannedAction
from app.schemas.common import AnalysisStatus, RiskLevel, RiskReason
from app.schemas.profile import FollowUpQuestion
from app.schemas.program import RuleOperator


class FailedRule(BaseModel):
    rule_id: str
    field: str
    operator: RuleOperator
    expected_value: Any
    actual_value: Any
    description: str


class UnevaluatedRule(BaseModel):
    rule_id: str
    field: str
    reason: str


class EligibilityResult(BaseModel):
    program_id: str
    eligible: bool | None
    status: AnalysisStatus
    failed_rules: list[FailedRule] = Field(default_factory=list)
    unevaluated_rules: list[UnevaluatedRule] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    questions: list[FollowUpQuestion] = Field(default_factory=list)
    official_source_required: bool = False


class ContradictionResult(BaseModel):
    issues: list[AnalysisIssue] = Field(default_factory=list)


class AppliedReadinessRule(BaseModel):
    rule_id: str
    score_delta: float
    occurrences: int = Field(ge=1)
    message: str


class ReadinessResult(BaseModel):
    readiness_score: float | None = Field(default=None, ge=0, le=100)
    risk_level: RiskLevel
    blockers: list[AnalysisIssue] = Field(default_factory=list)
    applied_rules: list[AppliedReadinessRule] = Field(default_factory=list)


class RiskSignal(BaseModel):
    code: str
    level: RiskLevel
    explanation: str


class RiskResult(BaseModel):
    risk_level: RiskLevel
    risk_reason: RiskReason | None = None
    explanation: str
    signals: list[RiskSignal] = Field(default_factory=list)


class ActionPlanResult(BaseModel):
    actions: list[PlannedAction] = Field(default_factory=list)


class ExplanationResult(BaseModel):
    explanations: list[str] = Field(default_factory=list)
