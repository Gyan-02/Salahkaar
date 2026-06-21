from typing import Any

from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class CitizenProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "citizen_profiles"

    fields: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    conflicts: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    missing_fields: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    document_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

