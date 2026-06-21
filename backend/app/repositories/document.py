from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.repositories.base import Repository
from app.schemas.document import DocumentCreate


class DocumentRepository(Repository[Document]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Document)

    def create(self, data: DocumentCreate) -> Document:
        return self.add(Document(**data.model_dump()))

    def list_by_type(self, document_type: str) -> list[Document]:
        statement = select(Document).where(Document.document_type == document_type)
        return list(self.session.scalars(statement))

