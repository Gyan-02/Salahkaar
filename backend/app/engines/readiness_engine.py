from pathlib import Path

from pydantic import ValidationError

from app.config.paths import DATA_PATH
from app.schemas.analysis import AnalysisIssue
from app.schemas.common import AnalysisStatus, RiskLevel
from app.schemas.engine import (
    AppliedReadinessRule,
    ContradictionResult,
    EligibilityResult,
    ReadinessResult,
)
from app.schemas.profile import BuiltProfile
from app.schemas.program import ReadinessConfiguration, ReadinessRuleDefinition


class ReadinessEngineError(RuntimeError):
    pass


class ReadinessEngine:
    """Applies transparent product heuristics; it does not decide eligibility."""

    def __init__(self, path: Path | None = None) -> None:
        config_path = path or DATA_PATH / "readiness_rules.json"
        try:
            self.configuration = ReadinessConfiguration.model_validate_json(
                config_path.read_text(encoding="utf-8")
            )
        except (FileNotFoundError, ValidationError) as exc:
            raise ReadinessEngineError(f"Invalid readiness configuration: {exc}") from exc

    def check(
        self,
        profile: BuiltProfile,
        eligibility: EligibilityResult,
        contradictions: ContradictionResult,
        document_quality: list[str] | None = None,
    ) -> ReadinessResult:
        if eligibility.status == AnalysisStatus.OFFICIAL_RULES_PENDING:
            return ReadinessResult(
                readiness_score=None,
                risk_level=RiskLevel.PENDING,
                blockers=[],
                applied_rules=[],
            )
        score = self.configuration.starting_score
        applied: list[AppliedReadinessRule] = []
        blockers: list[AnalysisIssue] = []
        qualities = document_quality or []

        for rule in self.configuration.rules:
            if not rule.enabled:
                continue
            matching_issues, occurrences = self._matches(
                rule, profile, eligibility, contradictions, qualities
            )
            if occurrences == 0:
                continue
            total_delta = rule.score_delta * occurrences
            score += total_delta
            applied.append(
                AppliedReadinessRule(
                    rule_id=rule.id,
                    score_delta=total_delta,
                    occurrences=occurrences,
                    message=rule.message,
                )
            )
            if rule.blocker:
                if matching_issues:
                    blockers.extend(matching_issues)
                else:
                    blockers.append(
                        AnalysisIssue(
                            code=rule.id,
                            category="readiness",
                            severity=RiskLevel.HIGH,
                            message=rule.message,
                        )
                    )

        bounded_score = max(0.0, min(100.0, score))
        return ReadinessResult(
            readiness_score=bounded_score,
            risk_level=self._risk_band(bounded_score),
            blockers=self._deduplicate_issues(blockers),
            applied_rules=applied,
        )

    @staticmethod
    def _matches(
        rule: ReadinessRuleDefinition,
        profile: BuiltProfile,
        eligibility: EligibilityResult,
        contradictions: ContradictionResult,
        qualities: list[str],
    ) -> tuple[list[AnalysisIssue], int]:
        condition = rule.condition
        if "issue_severity" in condition:
            level = str(condition["issue_severity"])
            issues = [
                issue for issue in contradictions.issues if issue.severity.value == level
            ]
            return issues, len(issues)
        if condition.get("missing_required_field") is True:
            return [], len(set(eligibility.missing_fields))
        if condition.get("failed_eligibility_rule") is True:
            return [], len(eligibility.failed_rules)
        if "document_quality" in condition:
            expected = str(condition["document_quality"]).upper()
            return [], sum(quality.upper() == expected for quality in qualities)
        raise ReadinessEngineError(f"Unsupported readiness condition: {condition}")

    def _risk_band(self, score: float) -> RiskLevel:
        for level in (RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH):
            minimum, maximum = self.configuration.risk_bands[level.value]
            if minimum <= score <= maximum:
                return level
        raise ReadinessEngineError(f"Readiness score {score} is outside configured bands")

    @staticmethod
    def _deduplicate_issues(issues: list[AnalysisIssue]) -> list[AnalysisIssue]:
        unique: dict[tuple[str, str], AnalysisIssue] = {}
        for issue in issues:
            unique.setdefault((issue.code, issue.message), issue)
        return list(unique.values())
