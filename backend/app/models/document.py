from typing import Any

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    document_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    extracted_fields: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    extractor: Mapped[str] = mapped_column(String(50), nullable=False)
    extraction_status: Mapped[str] = mapped_column(String(30), nullable=False)
    extraction_failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

