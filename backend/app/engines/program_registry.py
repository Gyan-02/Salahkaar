from pathlib import Path

from pydantic import ValidationError

from app.config.paths import DATA_PATH
from app.schemas.program import ProgramDefinition, ProgramsConfiguration


class ProgramRegistryError(RuntimeError):
    pass


class ProgramNotFoundError(ProgramRegistryError):
    pass


class ProgramRegistry:
    """Loads and validates every supported program from configuration."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DATA_PATH / "programs.json"
        self._configuration = self._load()
        self._programs = {program.id: program for program in self._configuration.programs}
        if len(self._programs) != len(self._configuration.programs):
            raise ProgramRegistryError("programs.json contains duplicate program ids")

    def _load(self) -> ProgramsConfiguration:
        try:
            return ProgramsConfiguration.model_validate_json(
                self.path.read_text(encoding="utf-8")
            )
        except FileNotFoundError as exc:
            raise ProgramRegistryError(f"Program configuration not found: {self.path}") from exc
        except ValidationError as exc:
            raise ProgramRegistryError(f"Invalid program configuration: {exc}") from exc

    def get_program(self, program_id: str) -> ProgramDefinition:
        try:
            return self._programs[program_id]
        except KeyError as exc:
            raise ProgramNotFoundError(f"Unknown program: {program_id}") from exc

    def list_programs(self) -> list[ProgramDefinition]:
        return list(self._configuration.programs)

    def validate_program(self, program_id: str) -> bool:
        return program_id in self._programs
