from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


RuleOperator = Literal["==", "!=", "<", "<=", ">", ">=", "contains"]
PolicyStatus = Literal[
    "ACTIVE_RULES", "PARTIAL_RULES_ACTIVE", "OFFICIAL_RULES_PENDING"
]


class EligibilityRule(BaseModel):
    id: str
    field: str
    operator: RuleOperator
    value: Any
    description: str
    enabled: bool = True
    official_source: str


class FollowUpDefinition(BaseModel):
    field: str
    question: str


class OfficialRequirement(BaseModel):
    value: Any
    marker: Literal["# OFFICIAL_SOURCE_REQUIRED"]
    needed: str


class ProgramDefinition(BaseModel):
    id: str
    name: str
    description: str
    official_data_status: Literal[
        "verified", "partially_verified", "official_source_required"
    ]
    eligibility_rules_complete: bool = False
    policy_status: PolicyStatus = "OFFICIAL_RULES_PENDING"
    demo_jurisdiction: str | None = None
    baseline_reference_dataset: str | None = None
    program_active: bool | None = None
    program_active_marker: Literal["# OFFICIAL_SOURCE_REQUIRED"] | None = None
    program_active_note: str | None = None
    last_verified: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    official_sources: list[str] = Field(default_factory=list)
    official_requirements: dict[str, OfficialRequirement] = Field(default_factory=dict)
    required_documents: list[str] = Field(default_factory=list)
    required_profile_fields: list[str] = Field(default_factory=list)
    follow_up_questions: list[FollowUpDefinition] = Field(default_factory=list)
    eligibility_rules: list[EligibilityRule] = Field(default_factory=list)

    @model_validator(mode="after")
    def reject_placeholder_enabled_rules(self) -> "ProgramDefinition":
        if self.policy_status == "OFFICIAL_RULES_PENDING":
            if self.eligibility_rules_complete:
                raise ValueError("Pending programs cannot mark eligibility rules complete")
            if any(rule.enabled for rule in self.eligibility_rules):
                raise ValueError("Pending programs cannot contain enabled eligibility rules")
        for rule in self.eligibility_rules:
            if not rule.enabled:
                continue
            if rule.value == "PLACEHOLDER" or "OFFICIAL_SOURCE_REQUIRED" in rule.official_source:
                raise ValueError("Enabled eligibility rules cannot use placeholders")
        return self


class ProgramsConfiguration(BaseModel):
    schema_version: str
    official_source_required: bool
    programs: list[ProgramDefinition]


class ContradictionRuleDefinition(BaseModel):
    id: str
    type: str
    fields: list[str]
    document_types: list[str] = Field(default_factory=list)
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    message: str
    enabled: bool = True


class ReadinessRuleDefinition(BaseModel):
    id: str
    condition: dict[str, Any]
    score_delta: float
    blocker: bool
    message: str
    enabled: bool = True


class ActionDefinition(BaseModel):
    id: str
    trigger: dict[str, Any]
    priority: int = Field(ge=1)
    instruction: str
    enabled: bool = True


class ContradictionsConfiguration(BaseModel):
    schema_version: str
    rules: list[ContradictionRuleDefinition]


class ReadinessConfiguration(BaseModel):
    schema_version: str
    policy_note: str
    starting_score: float = Field(ge=0, le=100)
    risk_bands: dict[Literal["LOW", "MEDIUM", "HIGH"], tuple[float, float]]
    rules: list[ReadinessRuleDefinition]


class ActionsConfiguration(BaseModel):
    schema_version: str
    actions: list[ActionDefinition]


class DocumentFieldDefinition(BaseModel):
    type: str
    required: bool
    sensitive: bool = False
    profile_field: str | None = None


class DocumentTypeDefinition(BaseModel):
    fields: dict[str, DocumentFieldDefinition]
    user_action_required: str | None = None


class DocumentSchemasConfiguration(BaseModel):
    schema_version: str
    document_types: dict[str, DocumentTypeDefinition]
