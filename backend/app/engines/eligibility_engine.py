from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from app.engines.program_registry import ProgramRegistry
from app.schemas.common import AnalysisStatus
from app.schemas.engine import EligibilityResult, FailedRule, UnevaluatedRule
from app.schemas.profile import BuiltProfile, FollowUpQuestion
from app.schemas.program import EligibilityRule


class RuleEvaluationError(ValueError):
    pass


class EligibilityEngine:
    """Evaluates only enabled, officially verified, data-defined rules."""

    def __init__(self, registry: ProgramRegistry) -> None:
        self.registry = registry

    def check(
        self,
        program_id: str,
        profile: BuiltProfile,
        answers: dict[str, Any] | None = None,
    ) -> EligibilityResult:
        program = self.registry.get_program(program_id)
        if program.policy_status == "OFFICIAL_RULES_PENDING":
            return EligibilityResult(
                program_id=program.id,
                eligible=None,
                status=AnalysisStatus.OFFICIAL_RULES_PENDING,
                failed_rules=[],
                unevaluated_rules=[],
                missing_fields=[],
                questions=[],
                official_source_required=True,
            )
        answers = answers or {}
        enabled_rules = [rule for rule in program.eligibility_rules if rule.enabled]
        missing_fields: list[str] = []
        questions: list[FollowUpQuestion] = []
        failed: list[FailedRule] = []
        unevaluated: list[UnevaluatedRule] = []

        question_by_field = {
            definition.field: definition.question
            for definition in program.follow_up_questions
        }
        for field in program.required_profile_fields:
            field_value, reason = self._read_value(field, profile, answers)
            if reason == "The required value is missing":
                missing_fields.append(field)
                questions.append(
                    FollowUpQuestion(
                        field=field,
                        question=question_by_field.get(
                            field, f"Please provide the value for {field.replace('_', ' ')}."
                        ),
                        required_for_program=program.id,
                    )
                )

        for rule in enabled_rules:
            actual, reason = self._read_value(rule.field, profile, answers)
            if reason is not None:
                unevaluated.append(
                    UnevaluatedRule(rule_id=rule.id, field=rule.field, reason=reason)
                )
                continue
            try:
                passed = self._evaluate(rule, actual)
            except RuleEvaluationError as exc:
                unevaluated.append(
                    UnevaluatedRule(rule_id=rule.id, field=rule.field, reason=str(exc))
                )
                continue
            if not passed:
                failed.append(
                    FailedRule(
                        rule_id=rule.id,
                        field=rule.field,
                        operator=rule.operator,
                        expected_value=rule.value,
                        actual_value=actual,
                        description=rule.description,
                    )
                )

        if failed:
            eligible: bool | None = False
            status = AnalysisStatus.INELIGIBLE
        elif (
            not enabled_rules
            or not program.eligibility_rules_complete
            or unevaluated
            or missing_fields
        ):
            eligible = None
            status = (
                AnalysisStatus.INFORMATION_REQUIRED
                if unevaluated or missing_fields
                else AnalysisStatus.PARTIAL_RULES_EVALUATED
            )
        else:
            eligible = True
            status = AnalysisStatus.ELIGIBLE

        return EligibilityResult(
            program_id=program.id,
            eligible=eligible,
            status=status,
            failed_rules=failed,
            unevaluated_rules=unevaluated,
            missing_fields=list(dict.fromkeys(missing_fields)),
            questions=questions,
            official_source_required=not program.eligibility_rules_complete,
        )

    @staticmethod
    def _read_value(
        field: str,
        profile: BuiltProfile,
        answers: dict[str, Any],
    ) -> tuple[Any, str | None]:
        profile_field = profile.fields.get(field)
        if profile_field is not None:
            if profile_field.conflicted:
                return None, "The field has conflicting document values"
            if profile_field.value is not None:
                return profile_field.value, None
        if field in answers and answers[field] is not None:
            return answers[field], None
        return None, "The required value is missing"

    @classmethod
    def _evaluate(cls, rule: EligibilityRule, actual: Any) -> bool:
        expected = rule.value
        if rule.operator == "==":
            return cls._equality_key(actual) == cls._equality_key(expected)
        if rule.operator == "!=":
            return cls._equality_key(actual) != cls._equality_key(expected)
        if rule.operator == "contains":
            if isinstance(actual, str) and isinstance(expected, str):
                return expected.casefold() in actual.casefold()
            try:
                return expected in actual
            except TypeError as exc:
                raise RuleEvaluationError("contains requires a collection value") from exc

        left, right = cls._ordered_values(actual, expected)
        operations = {
            "<": lambda: left < right,
            "<=": lambda: left <= right,
            ">": lambda: left > right,
            ">=": lambda: left >= right,
        }
        return operations[rule.operator]()

    @staticmethod
    def _equality_key(value: Any) -> Any:
        if isinstance(value, str):
            return " ".join(value.split()).casefold()
        return value

    @staticmethod
    def _ordered_values(actual: Any, expected: Any) -> tuple[Any, Any]:
        try:
            return Decimal(str(actual)), Decimal(str(expected))
        except (InvalidOperation, ValueError):
            pass
        if isinstance(actual, str) and isinstance(expected, str):
            try:
                return date.fromisoformat(actual), date.fromisoformat(expected)
            except ValueError:
                pass
        raise RuleEvaluationError("Ordered comparisons require numbers or ISO dates")
