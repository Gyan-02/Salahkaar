import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.config.paths import DATA_PATH
from app.schemas.analysis import AnalysisIssue
from app.schemas.common import RiskLevel
from app.schemas.engine import ContradictionResult
from app.schemas.profile import BuiltProfile, ProvenanceValue
from app.schemas.program import ContradictionRuleDefinition, ContradictionsConfiguration


class ContradictionEngineError(RuntimeError):
    pass


class ContradictionEngine:
    def __init__(self, path: Path | None = None, today: date | None = None) -> None:
        config_path = path or DATA_PATH / "contradictions.json"
        try:
            self.configuration = ContradictionsConfiguration.model_validate_json(
                config_path.read_text(encoding="utf-8")
            )
        except (FileNotFoundError, ValidationError) as exc:
            raise ContradictionEngineError(
                f"Invalid contradiction configuration: {exc}"
            ) from exc
        self.today = today or date.today()

    def check(self, profile: BuiltProfile) -> ContradictionResult:
        issues: list[AnalysisIssue] = []
        seen_mismatches: set[str] = set()
        rules = sorted(
            (rule for rule in self.configuration.rules if rule.enabled),
            key=lambda rule: len(rule.document_types),
            reverse=True,
        )
        for rule in rules:
            if rule.type == "field_mismatch":
                for field in rule.fields:
                    issue = self._mismatch_issue(rule, field, profile)
                    if issue is None or field in seen_mismatches:
                        continue
                    issues.append(issue)
                    seen_mismatches.add(field)
            elif rule.type == "date_expired":
                issues.extend(self._expired_issues(rule, profile))
            else:
                raise ContradictionEngineError(
                    f"Unsupported contradiction rule type: {rule.type}"
                )
        return ContradictionResult(issues=issues)

    def _mismatch_issue(
        self,
        rule: ContradictionRuleDefinition,
        field: str,
        profile: BuiltProfile,
    ) -> AnalysisIssue | None:
        profile_field = profile.fields.get(field)
        if profile_field is None:
            return None
        values = profile_field.values
        if rule.document_types:
            values = [value for value in values if value.source in rule.document_types]
            present_sources = {value.source for value in values}
            if not set(rule.document_types).issubset(present_sources):
                return None
        if len({self._comparison_key(field, value.value) for value in values}) < 2:
            return None
        return AnalysisIssue(
            code=rule.id,
            category="contradiction",
            severity=RiskLevel(rule.severity),
            message=rule.message,
            evidence=[self._evidence(field, value) for value in values],
        )

    def _expired_issues(
        self,
        rule: ContradictionRuleDefinition,
        profile: BuiltProfile,
    ) -> list[AnalysisIssue]:
        issues: list[AnalysisIssue] = []
        for field in rule.fields:
            profile_field = profile.fields.get(field)
            if profile_field is None:
                continue
            for value in profile_field.values:
                if rule.document_types and value.source not in rule.document_types:
                    continue
                parsed = self._date_value(value.value)
                if parsed is None or parsed >= self.today:
                    continue
                issues.append(
                    AnalysisIssue(
                        code=rule.id,
                        category="contradiction",
                        severity=RiskLevel(rule.severity),
                        message=rule.message,
                        evidence=[self._evidence(field, value)],
                    )
                )
        return issues

    @staticmethod
    def _date_value(value: Any) -> date | None:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                return None
        return None

    @staticmethod
    def _comparison_key(field: str, value: Any) -> str:
        if isinstance(value, str):
            normalized = value.casefold()
            if field == "address":
                normalized = re.sub(r"[^\w\s]", " ", normalized)
            normalized = " ".join(normalized.split())
        else:
            normalized = value
        return json.dumps(normalized, sort_keys=True, default=str, ensure_ascii=False)

    @staticmethod
    def _evidence(field: str, value: ProvenanceValue) -> dict[str, Any]:
        return {
            "field": field,
            "value": value.value,
            "source": value.source,
            "document_id": value.document_id,
        }
