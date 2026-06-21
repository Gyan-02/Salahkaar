import json

import pytest

from app.engines.program_registry import (
    ProgramNotFoundError,
    ProgramRegistry,
    ProgramRegistryError,
)


def test_registry_lists_locked_programs(registry: ProgramRegistry) -> None:
    assert [program.id for program in registry.list_programs()] == [
        "pm-kisan",
        "nmmss",
        "ayushman-bharat-pm-jay",
    ]
    assert registry.validate_program("pm-kisan") is True
    assert registry.validate_program("unknown") is False


def test_registry_exposes_policy_states(registry: ProgramRegistry) -> None:
    assert registry.get_program("pm-kisan").policy_status == "PARTIAL_RULES_ACTIVE"
    assert registry.get_program("nmmss").policy_status == "PARTIAL_RULES_ACTIVE"
    pmjay = registry.get_program("ayushman-bharat-pm-jay")
    assert pmjay.policy_status == "OFFICIAL_RULES_PENDING"
    assert pmjay.demo_jurisdiction == "Bihar"
    assert pmjay.eligibility_rules == []


def test_registry_rejects_unknown_program(registry: ProgramRegistry) -> None:
    with pytest.raises(ProgramNotFoundError, match="Unknown program"):
        registry.get_program("not-real")


def test_registry_rejects_duplicate_ids(tmp_path, registry: ProgramRegistry) -> None:
    payload = json.loads(registry.path.read_text(encoding="utf-8"))
    payload["programs"].append(payload["programs"][0])
    path = tmp_path / "programs.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ProgramRegistryError, match="duplicate program ids"):
        ProgramRegistry(path)


def test_pending_program_cannot_enable_rules(tmp_path, registry: ProgramRegistry) -> None:
    payload = json.loads(registry.path.read_text(encoding="utf-8"))
    pmjay = next(p for p in payload["programs"] if p["id"] == "ayushman-bharat-pm-jay")
    pmjay["eligibility_rules"] = [
        {
            "id": "forbidden",
            "field": "placeholder",
            "operator": "==",
            "value": True,
            "description": "Must be rejected",
            "enabled": True,
            "official_source": "https://example.invalid",
        }
    ]
    path = tmp_path / "programs.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ProgramRegistryError, match="Pending programs cannot"):
        ProgramRegistry(path)

