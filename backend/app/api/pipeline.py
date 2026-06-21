from dataclasses import dataclass

from app.engines import (
    ActionPlanner,
    ContradictionEngine,
    EligibilityEngine,
    ExplanationEngine,
    ProfileBuilder,
    ProgramRegistry,
    ReadinessEngine,
    RiskEngine,
)
from app.schemas.analysis import AnalysisIssue, AnalysisResult
from app.schemas.api import AnalysisRunRequest
from app.schemas.common import RiskLevel
from app.schemas.document import ExtractionInput, ExtractionResult
from app.schemas.engine import (
    ActionPlanResult,
    ContradictionResult,
    EligibilityResult,
    ExplanationResult,
    ReadinessResult,
    RiskResult,
)
from app.schemas.profile import BuiltProfile, ProfileDocument
from app.services.extraction.mock import MockExtractor


@dataclass(slots=True)
class PipelineExecution:
    request: AnalysisRunRequest
    extracted_documents: list[ExtractionResult]
    profile: BuiltProfile
    eligibility: EligibilityResult
    contradictions: ContradictionResult
    readiness: ReadinessResult
    risk: RiskResult
    action_plan: ActionPlanResult
    explanations: ExplanationResult
    result: AnalysisResult


class AnalysisPipeline:
    """One shared, Mock-only execution path for all Phase 8 endpoints."""

    def __init__(self, explanation_engine: ExplanationEngine | None = None) -> None:
        self.registry = ProgramRegistry()
        self.profile_builder = ProfileBuilder()
        self.eligibility_engine = EligibilityEngine(self.registry)
        self.contradiction_engine = ContradictionEngine()
        self.readiness_engine = ReadinessEngine()
        self.risk_engine = RiskEngine()
        self.action_planner = ActionPlanner()
        self.explanation_engine = explanation_engine or ExplanationEngine()
        self.extractor = MockExtractor()

    async def run(self, request: AnalysisRunRequest) -> PipelineExecution:
        program = self.registry.get_program(request.program_id)
        extracted: list[ExtractionResult] = []
        profile_documents: list[ProfileDocument] = []

        for index, document in enumerate(request.documents, start=1):
            filename = document.filename or f"{document.document_type}-{index}.json"
            extraction = await self.extractor.extract(
                ExtractionInput(
                    filename=filename,
                    content_type="application/json",
                    content=b"",
                    document_type=document.document_type,
                    mock_fields=document.fields,
                )
            )
            extracted.append(extraction)
            profile_documents.append(
                ProfileDocument(
                    document_type=extraction.document_type,
                    fields=extraction.fields,
                    document_id=document.document_id or filename,
                )
            )

        profile = self.profile_builder.build(
            profile_documents,
            required_fields=program.required_profile_fields,
        )
        eligibility = self.eligibility_engine.check(
            program.id,
            profile,
            request.answers,
        )
        contradictions = self.contradiction_engine.check(profile)
        readiness = self.readiness_engine.check(
            profile,
            eligibility,
            contradictions,
            request.document_quality,
        )
        risk = self.risk_engine.assess(
            profile,
            eligibility,
            contradictions,
            readiness,
            request.document_quality,
        )
        action_plan = self.action_planner.plan(
            program.id,
            profile,
            eligibility,
            contradictions,
            readiness,
            risk,
        )
        eligibility_issues = self._eligibility_issues(eligibility)
        explanations = self.explanation_engine.explain(
            program.name,
            eligibility,
            contradictions,
            readiness,
            risk,
            action_plan,
            program_id=program.id,
            additional_issues=eligibility_issues,
        )
        issues = [*contradictions.issues, *eligibility_issues]
        result = AnalysisResult(
            program=program.id,
            status=eligibility.status,
            eligible=eligibility.eligible,
            readiness_score=readiness.readiness_score,
            risk_level=risk.risk_level,
            risk_reason=risk.risk_reason,
            issues=issues,
            blockers=readiness.blockers,
            actions=action_plan.actions,
            questions=eligibility.questions,
            explanations=explanations.explanations,
        )
        return PipelineExecution(
            request=request,
            extracted_documents=extracted,
            profile=profile,
            eligibility=eligibility,
            contradictions=contradictions,
            readiness=readiness,
            risk=risk,
            action_plan=action_plan,
            explanations=explanations,
            result=result,
        )

    @staticmethod
    def _eligibility_issues(eligibility: EligibilityResult) -> list[AnalysisIssue]:
        return [
            AnalysisIssue(
                code=rule.rule_id,
                category="eligibility",
                severity=RiskLevel.HIGH,
                message=rule.description,
                evidence=[
                    {
                        "field": rule.field,
                        "actual_value": rule.actual_value,
                        "operator": rule.operator,
                        "expected_value": rule.expected_value,
                    }
                ],
            )
            for rule in eligibility.failed_rules
        ]
