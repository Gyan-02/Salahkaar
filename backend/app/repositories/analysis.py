from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.repositories.base import Repository
from app.schemas.analysis import AnalysisCreate


class AnalysisRepository(Repository[Analysis]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Analysis)

    def create(self, data: AnalysisCreate) -> Analysis:
        payload = data.model_dump(mode="json")
        return self.add(Analysis(**payload))

    def list_for_profile(self, citizen_profile_id: str) -> list[Analysis]:
        statement = (
            select(Analysis)
            .where(Analysis.citizen_profile_id == citizen_profile_id)
            .order_by(Analysis.created_at.desc())
        )
        return list(self.session.scalars(statement))

