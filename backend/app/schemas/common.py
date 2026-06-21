from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampedRead(ORMModel):
    id: str
    created_at: datetime
    updated_at: datetime


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    PENDING = "PENDING"


class AnalysisStatus(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    INFORMATION_REQUIRED = "INFORMATION_REQUIRED"
    PARTIAL_RULES_EVALUATED = "PARTIAL_RULES_EVALUATED"
    OFFICIAL_RULES_PENDING = "OFFICIAL_RULES_PENDING"


class RiskReason(StrEnum):
    POLICY_INCOMPLETE = "POLICY_INCOMPLETE"
    DOCUMENT_BLOCKERS = "DOCUMENT_BLOCKERS"
    ELIGIBILITY_FAILURE = "ELIGIBILITY_FAILURE"
    MULTIPLE_FACTORS = "MULTIPLE_FACTORS"


class ExtractionStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FALLBACK_SUCCEEDED = "FALLBACK_SUCCEEDED"
    FAILED = "FAILED"
