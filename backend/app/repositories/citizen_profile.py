from sqlalchemy.orm import Session

from app.models.citizen_profile import CitizenProfile
from app.repositories.base import Repository
from app.schemas.profile import CitizenProfileCreate


class CitizenProfileRepository(Repository[CitizenProfile]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, CitizenProfile)

    def create(self, data: CitizenProfileCreate) -> CitizenProfile:
        return self.add(CitizenProfile(**data.model_dump()))

