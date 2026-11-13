from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    TIMESTAMP,
    VARCHAR,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.utils import get_utc_now

from .base import Base

if TYPE_CHECKING:
    from .session import Session


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(VARCHAR(length=256), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(Text)
    # What the bot remembers about the user from past calls: one fact per line
    # ("- Name is Sara"). Written after each call, read into the system prompt.
    facts: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=get_utc_now, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        onupdate=get_utc_now,
        nullable=False,
        default=get_utc_now,
        index=True,
    )

    sessions: Mapped[list["Session"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
