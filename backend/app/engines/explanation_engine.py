from collections.abc import Callable

from app.schemas.analysis import AnalysisIssue, OfficialReference
from app.schemas.common import AnalysisStatus
from app.schemas.engine import (
    ActionPlanResult,
    ContradictionResult,
    EligibilityResult,
    ExplanationResult,
    ReadinessResult,
    RiskResult,
)


class ExplanationEngine:
    """Produces deterministic, evidence-oriented explanations without an LLM."""

    def __init__(
        self,
        reference_resolver: Callable[[str, str], OfficialReference | None] | None = None,
    ) -> None:
        self.reference_resolver = reference_resolver

    def explain(
        self,
        program_name: str,
        eligibility: EligibilityResult,
        contradictions: ContradictionResult,
        readiness: ReadinessResult,
        risk: RiskResult,
        action_plan: ActionPlanResult,
        program_id: str | None = None,
        additional_issues: list[AnalysisIssue] | None = None,
    ) -> ExplanationResult:
        self._attach_official_references(
            program_id=program_id,
            issues=[
                *contradictions.issues,
                *readiness.blockers,
                *(additional_issues or []),
            ],
        )
        explanations: list[str] = []

        if eligibility.status == AnalysisStatus.OFFICIAL_RULES_PENDING:
            explanations.append(
                f"# OFFICIAL_SOURCE_REQUIRED: verified eligibility rules for {program_name} are pending; no eligibility, readiness, risk, or action result was computed."
            )
        elif eligibility.eligible is True:
            explanations.append(
                f"The supplied information passes every enabled rule for {program_name}."
            )
        elif eligibility.eligible is False:
            explanations.append(
                f"The supplied information fails {len(eligibility.failed_rules)} enabled rule(s) for {program_name}."
            )
            explanations.extend(rule.description for rule in eligibility.failed_rules)
        elif eligibility.official_source_required:
            explanations.append(
                f"# OFFICIAL_SOURCE_REQUIRED: eligibility for {program_name} is unknown because the complete verified rule set is not configured."
            )
        else:
            explanations.append(
                f"Eligibility for {program_name} is unknown because required information is incomplete or conflicted."
            )

        for issue in contradictions.issues:
            sources = sorted(
                {
                    str(item.get("source"))
                    for item in issue.evidence
                    if item.get("source")
                }
            )
            source_text = f" Sources: {', '.join(sources)}." if sources else ""
            explanations.append(f"{issue.message}{source_text}")

        explanations.extend(
            self._readiness_explanations(readiness, eligibility, contradictions)
        )
        if eligibility.official_source_required and readiness.readiness_score is not None:
            explanations.append(
                f"Overall risk is {risk.risk_level.value} because the complete official eligibility rule set is unavailable. This assessment-completeness risk does not reduce the readiness score."
            )
        else:
            explanations.append(risk.explanation)
        contradiction_codes = {issue.code for issue in contradictions.issues}
        scored_signal_codes = {
            "low_document_quality",
            "missing_information",
            "failed_eligibility_rules",
            "official_source_required",
        }
        explanations.extend(
            signal.explanation
            for signal in risk.signals
            if signal.code not in contradiction_codes
            and signal.code not in scored_signal_codes
        )
        if action_plan.actions:
            explanations.append(
                f"The action plan contains {len(action_plan.actions)} prioritized step(s)."
            )

        return ExplanationResult(explanations=self._deduplicate(explanations))

    @staticmethod
    def _deduplicate(items: list[str]) -> list[str]:
        return list(dict.fromkeys(item for item in items if item))

    def _attach_official_references(
        self,
        program_id: str | None,
        issues: list[AnalysisIssue],
    ) -> None:
        if self.reference_resolver is None or program_id is None:
            return
        resolved: dict[str, OfficialReference | None] = {}
        for issue in issues:
            if issue.code not in resolved:
                resolved[issue.code] = self.reference_resolver(program_id, issue.code)
            issue.official_reference = resolved[issue.code]

    @staticmethod
    def _readiness_explanations(
        readiness: ReadinessResult,
        eligibility: EligibilityResult,
        contradictions: ContradictionResult,
    ) -> list[str]:
        if readiness.readiness_score is None:
            return ["Readiness was not computed while official rules are pending."]
        lines: list[str] = []
        if not readiness.applied_rules:
            lines.append(
                "No readiness points were deducted: no configured document, information, eligibility, or quality blockers were detected."
            )
        for applied in readiness.applied_rules:
            points = abs(applied.score_delta)
            count = applied.occurrences
            if applied.rule_id in {
                "high_severity_contradiction",
                "medium_severity_contradiction",
            }:
                severity = (
                    "HIGH"
                    if applied.rule_id == "high_severity_contradiction"
                    else "MEDIUM"
                )
                issues = [
                    issue.message.rstrip(".")
                    for issue in contradictions.issues
                    if issue.severity.value == severity
                ]
                noun = "contradiction" if count == 1 else "contradictions"
                detail = f"{count} {severity}-severity {noun}"
                if issues:
                    detail += f" — {'; '.join(issues)}"
            elif applied.rule_id == "missing_required_information":
                noun = "field" if count == 1 else "fields"
                detail = f"{count} missing required {noun}"
                if eligibility.missing_fields:
                    detail += f" — {', '.join(eligibility.missing_fields)}"
            elif applied.rule_id == "failed_eligibility_rule":
                noun = "rule" if count == 1 else "rules"
                detail = f"{count} failed verified eligibility {noun}"
                descriptions = [
                    rule.description.rstrip(".") for rule in eligibility.failed_rules
                ]
                if descriptions:
                    detail += f" — {'; '.join(descriptions)}"
            elif applied.rule_id == "low_document_quality":
                noun = "document" if count == 1 else "documents"
                detail = f"{count} low-quality {noun}"
            else:
                detail = applied.message
            point_word = "point" if points == 1 else "points"
            lines.append(
                f"Score reduced by {points:g} {point_word}: {detail}."
            )
        lines.append(
            f"Final readiness score: {readiness.readiness_score:g}/100 ({readiness.risk_level.value})."
        )
        return lines
