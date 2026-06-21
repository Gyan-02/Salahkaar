from abc import ABC, abstractmethod

from app.schemas.document import ExtractionInput, ExtractionResult


class ExtractionError(RuntimeError):
    pass


class DocumentExtractor(ABC):
    @abstractmethod
    async def extract(self, document: ExtractionInput) -> ExtractionResult:
        """Extract a typed field map without persisting the source file."""
        raise NotImplementedError

