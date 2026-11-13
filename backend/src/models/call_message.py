from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, VARCHAR, Enum, ForeignKey, Integer, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.utils import get_utc_now

from .base import Base


class MessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class CallMessage(Base):
    """One transcript entry of a call, shaped like a chat message:

    - system:    content = the prompt the bot started the call with
    - user:      content = what the caller said
    - assistant: content = what the bot said, or tool_calls = the tools it called
    - tool:      content = a tool's result, for tool_call_id / tool_name
    """

    __tablename__ = "call_messages"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    call_id: Mapped[UUID] = mapped_column(
        ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(
            MessageRole,
            native_enum=False,
            length=16,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    content: Mapped[str | None] = mapped_column(Text)
    # [{"id": ..., "name": ..., "arguments": {...}}], on assistant tool-call messages.
    tool_calls: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    tool_call_id: Mapped[str | None] = mapped_column(VARCHAR(256))
    tool_name: Mapped[str | None] = mapped_column(VARCHAR(256))
    # Milliseconds since the call's pipeline started; orders the transcript.
    timestamp_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=get_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=get_utc_now,
        onupdate=get_utc_now,
    )
