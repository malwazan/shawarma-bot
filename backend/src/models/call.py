from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, VARCHAR, Enum, ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.core.utils import get_utc_now

from .base import Base


class CallStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Call(Base):
    """One voice call between a user and the bot.

    Created as in_progress when the user starts a call; the voice service sets
    the final status, ended_at and duration when the call ends.
    """

    __tablename__ = "calls"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_number: Mapped[str] = mapped_column(VARCHAR(256), nullable=False)  # username
    to_number: Mapped[str] = mapped_column(VARCHAR(256), nullable=False)  # agent name
    duration: Mapped[int | None] = mapped_column(
        Integer
    )  # seconds; set when the call ends
    status: Mapped[CallStatus] = mapped_column(
        # Stored as plain text (no Postgres enum type), so adding a status
        # later needs no migration.
        Enum(
            CallStatus,
            native_enum=False,
            length=16,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=CallStatus.IN_PROGRESS,
    )
    started_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=get_utc_now, index=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
