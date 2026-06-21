from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.config.paths import DATA_PATH
from app.schemas.common import AnalysisStatus
from app.schemas.engine import (
    ActionPlanResult,
    ContradictionResult,
    EligibilityResult,
    ReadinessResult,
    RiskResult,
)
from app.schemas.profile import BuiltProfile
from app.schemas.program import ActionDefinition, ActionsConfiguration
from app.schemas.analysis import PlannedAction


class ActionPlannerError(RuntimeError):
    pass


class ActionPlanner:
    def __init__(self, path: Path | None = None) -> None:
        config_path = path or DATA_PATH / "actions.json"
        try:
            self.configuration = ActionsConfiguration.model_validate_json(
                config_path.read_text(encoding="utf-8")
            )
        except (FileNotFoundError, ValidationError) as exc:
            raise ActionPlannerError(f"Invalid action configuration: {exc}") from exc

    def plan(
        self,
        program_id: str,
        profile: BuiltProfile,
        eligibility: EligibilityResult,
        contradictions: ContradictionResult,
        readiness: ReadinessResult,
        risk: RiskResult,
    ) -> ActionPlanResult:
        if eligibility.status == AnalysisStatus.OFFICIAL_RULES_PENDING:
            return ActionPlanResult(actions=[])
        planned: list[PlannedAction] = []
        for definition in self.configuration.actions:
            if not definition.enabled:
                continue
            reason = self._match_reason(
                definition,
                program_id,
                profile,
                eligibility,
                contradictions,
                readiness,
                risk,
            )
            if reason is None:
                continue
            planned.append(
                PlannedAction(
                    priority=definition.priority,
                    action_id=definition.id,
                    instruction=definition.instruction,
                    reason=reason,
                )
            )
        planned.sort(key=lambda action: action.priority)
        return ActionPlanResult(actions=planned)

    @staticmethod
    def _match_reason(
        definition: ActionDefinition,
        program_id: str,
        profile: BuiltProfile,
        eligibility: EligibilityResult,
        contradictions: ContradictionResult,
        readiness: ReadinessResult,
        risk: RiskResult,
    ) -> str | None:
        trigger = definition.trigger
        supported = {
            "program_id",
            "issue_id",
            "missing_required_field",
            "ready_to_submit",
            "risk_level",
            "eligibility",
        }
        unknown = set(trigger) - supported
        if unknown:
            raise ActionPlannerError(f"Unsupported action trigger keys: {sorted(unknown)}")
        if "program_id" in trigger and trigger["program_id"] != program_id:
            return None

        reasons: list[str] = []
        if "issue_id" in trigger:
            issue = next(
                (item for item in contradictions.issues if item.code == trigger["issue_id"]),
                None,
            )
            if issue is None:
                return None
            reasons.append(issue.message)
        if trigger.get("missing_required_field") is True:
            missing = set(eligibility.missing_fields)
            if not missing:
                return None
            reasons.append(f"Missing fields: {', '.join(sorted(missing))}.")
        if "risk_level" in trigger:
            if risk.risk_level.value != trigger["risk_level"]:
                return None
            reasons.append(risk.explanation)
        if "eligibility" in trigger:
            if eligibility.eligible is not trigger["eligibility"]:
                return None
            reasons.append("The configured eligibility state matches this action.")
        if trigger.get("ready_to_submit") is True:
            ready = (
                eligibility.eligible is True
                and not readiness.blockers
                and risk.risk_level.value == "LOW"
            )
            if not ready:
                return None
            reasons.append("No configured blockers remain.")
        if not trigger:
            return None
        return " ".join(reasons) or "Configured action condition matched."
