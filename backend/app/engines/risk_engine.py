from app.schemas.common import AnalysisStatus, RiskLevel, RiskReason
from app.schemas.engine import (
    ContradictionResult,
    EligibilityResult,
    ReadinessResult,
    RiskResult,
    RiskSignal,
)
from app.schemas.profile import BuiltProfile


class RiskEngine:
    """Summarizes known submission risk without changing eligibility results."""

    _RANK = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 1, RiskLevel.HIGH: 2}

    def assess(
        self,
        profile: BuiltProfile,
        eligibility: EligibilityResult,
        contradictions: ContradictionResult,
        readiness: ReadinessResult,
        document_quality: list[str] | None = None,
    ) -> RiskResult:
        if eligibility.status == AnalysisStatus.OFFICIAL_RULES_PENDING:
            return RiskResult(
                risk_level=RiskLevel.PENDING,
                risk_reason=RiskReason.POLICY_INCOMPLETE,
                explanation="Official eligibility rules are pending verification; risk was not computed.",
                signals=[],
            )
        signals: list[RiskSignal] = []
        missing_count = len(set(eligibility.missing_fields))

        if eligibility.official_source_required:
            signals.append(
                RiskSignal(
                    code="official_source_required",
                    level=RiskLevel.HIGH,
                    explanation="The complete official rule set is not configured, so eligibility cannot yet be determined.",
                )
            )
        if eligibility.failed_rules:
            signals.append(
                RiskSignal(
                    code="failed_eligibility_rules",
                    level=RiskLevel.HIGH,
                    explanation=f"{len(eligibility.failed_rules)} verified eligibility rule(s) failed.",
                )
            )
        for issue in contradictions.issues:
            signals.append(
                RiskSignal(code=issue.code, level=issue.severity, explanation=issue.message)
            )
        if missing_count:
            signals.append(
                RiskSignal(
                    code="missing_information",
                    level=RiskLevel.MEDIUM,
                    explanation=f"{missing_count} required field(s) are missing.",
                )
            )
        low_quality_count = sum(
            quality.upper() == "LOW" for quality in (document_quality or [])
        )
        if low_quality_count:
            signals.append(
                RiskSignal(
                    code="low_document_quality",
                    level=RiskLevel.MEDIUM,
                    explanation=f"{low_quality_count} document(s) have low extraction quality.",
                )
            )
        if readiness.blockers and not signals:
            signals.append(
                RiskSignal(
                    code="readiness_blockers",
                    level=RiskLevel.HIGH,
                    explanation=f"{len(readiness.blockers)} readiness blocker(s) remain.",
                )
            )

        risk_level = max(
            (signal.level for signal in signals),
            key=self._RANK.__getitem__,
            default=RiskLevel.LOW,
        )
        explanations = {
            RiskLevel.LOW: "No configured submission risk signals were detected.",
            RiskLevel.MEDIUM: "The application has issues that should be reviewed before submission.",
            RiskLevel.HIGH: "The application has blockers or cannot yet be assessed reliably.",
        }
        return RiskResult(
            risk_level=risk_level,
            risk_reason=self._risk_reason(
                eligibility=eligibility,
                contradictions=contradictions,
                missing_count=missing_count,
                low_quality_count=low_quality_count,
            ),
            explanation=explanations[risk_level],
            signals=signals,
        )

    @staticmethod
    def _risk_reason(
        eligibility: EligibilityResult,
        contradictions: ContradictionResult,
        missing_count: int,
        low_quality_count: int,
    ) -> RiskReason | None:
        categories: set[RiskReason] = set()
        if eligibility.official_source_required and eligibility.eligible is None:
            categories.add(RiskReason.POLICY_INCOMPLETE)
        if contradictions.issues or missing_count or low_quality_count:
            categories.add(RiskReason.DOCUMENT_BLOCKERS)
        if eligibility.eligible is False or eligibility.failed_rules:
            categories.add(RiskReason.ELIGIBILITY_FAILURE)
        if len(categories) > 1:
            return RiskReason.MULTIPLE_FACTORS
        return next(iter(categories), None)
