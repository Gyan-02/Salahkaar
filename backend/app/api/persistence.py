from sqlalchemy.orm import Session

from app.api.pipeline import PipelineExecution
from app.repositories.unit_of_work import UnitOfWork
from app.schemas.analysis import AnalysisCreate
from app.schemas.document import DocumentCreate
from app.schemas.profile import CitizenProfileCreate


def persist_execution(execution: PipelineExecution, session: Session) -> None:
    """Atomically persists structured extraction, profile and analysis JSON."""

    with UnitOfWork(session) as unit:
        document_ids: list[str] = []
        for payload, extraction in zip(
            execution.request.documents,
            execution.extracted_documents,
            strict=True,
        ):
            entity = unit.documents.create(
                DocumentCreate(
                    document_type=extraction.document_type,
                    original_filename=payload.filename or f"{payload.document_type}.json",
                    content_type="application/json",
                    extracted_fields=extraction.fields,
                    extractor=extraction.extractor,
                    extraction_status=extraction.status.value,
                    extraction_failure_reason=extraction.failure_reason,
                )
            )
            document_ids.append(entity.id)

        profile = unit.profiles.create(
            CitizenProfileCreate(
                fields={
                    name: field.model_dump(mode="json")
                    for name, field in execution.profile.fields.items()
                },
                conflicts=[
                    conflict.model_dump(mode="json")
                    for conflict in execution.profile.conflicts
                ],
                missing_fields=execution.profile.missing_fields,
                document_ids=document_ids,
            )
        )
        unit.analyses.create(
            AnalysisCreate(
                citizen_profile_id=profile.id,
                program_id=execution.request.program_id,
                eligible=execution.result.eligible,
                readiness_score=execution.result.readiness_score,
                risk_level=execution.result.risk_level,
                result=execution.result.model_dump(mode="json"),
            )
        )
