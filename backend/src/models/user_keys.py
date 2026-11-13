from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.core.utils import get_utc_now

from .base import Base


class UserKeys(Base):
    """A user's own API keys for the voice bot's services (one row per user).

    The key columns hold ciphertext (see src/core/crypto.py), never the keys
    themselves. A null column means that key hasn't been set.
    """

    __tablename__ = "user_keys"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    llm_key: Mapped[str | None] = mapped_column(Text)  # Gemini
    stt_key: Mapped[str | None] = mapped_column(Text)  # ElevenLabs speech to text
    tts_key: Mapped[str | None] = mapped_column(Text)  # ElevenLabs text to speech
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=get_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=get_utc_now,
        onupdate=get_utc_now,
    )
