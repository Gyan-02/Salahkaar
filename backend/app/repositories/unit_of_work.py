from types import TracebackType

from sqlalchemy.orm import Session

from app.repositories.analysis import AnalysisRepository
from app.repositories.citizen_profile import CitizenProfileRepository
from app.repositories.document import DocumentRepository


class UnitOfWork:
    """Coordinates repositories inside one caller-controlled transaction."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.documents = DocumentRepository(session)
        self.profiles = CitizenProfileRepository(session)
        self.analyses = AnalysisRepository(session)

    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is None:
            self.commit()
        else:
            self.rollback()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

