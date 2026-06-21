from typing import Any

from sqlalchemy import JSON, Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Analysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analyses"

    citizen_profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("citizen_profiles.id", ondelete="CASCADE"), index=True
    )
    program_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    eligible: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    readiness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    result: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

