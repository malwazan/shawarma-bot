"""Database queries of the voice module. Each function opens its own session."""

from typing import Any
from uuid import UUID

from sqlalchemy import select, update

from src.core.db.session import AsyncSessionMaker
from src.core.utils import get_utc_now
from src.models import Call, CallMessage, CallStatus, MessageRole, User, UserKeys
from src.user.keys import ApiKeys, decrypt_keys


async def get_keys_for_call(
    session_factory: AsyncSessionMaker, call_id: UUID
) -> ApiKeys:
    """The API keys of the user who made the call."""
    async with session_factory() as session:
        row = await session.scalar(
            select(UserKeys)
            .join(Call, Call.user_id == UserKeys.user_id)
            .where(Call.id == call_id)
        )
        return decrypt_keys(row)


async def get_facts_for_call(
    session_factory: AsyncSessionMaker, call_id: UUID
) -> str | None:
    """The stored facts of the user who made the call."""
    async with session_factory() as session:
        return await session.scalar(
            select(User.facts)
            .join(Call, Call.user_id == User.id)
            .where(Call.id == call_id)
        )


async def save_facts_for_call(
    session_factory: AsyncSessionMaker, call_id: UUID, facts: str | None
) -> None:
    """Replace the facts of the user who made the call."""
    async with session_factory() as session:
        user_id = select(Call.user_id).where(Call.id == call_id).scalar_subquery()
        await session.execute(
            update(User).where(User.id == user_id).values(facts=facts)
        )
        await session.commit()


async def get_conversation(
    session_factory: AsyncSessionMaker, call_id: UUID
) -> list[CallMessage]:
    """What the caller and the agent said, in order (no system or tool messages)."""
    async with session_factory() as session:
        messages = await session.scalars(
            select(CallMessage)
            .where(
                CallMessage.call_id == call_id,
                CallMessage.role.in_([MessageRole.USER, MessageRole.ASSISTANT]),
                CallMessage.content.is_not(None),
            )
            .order_by(CallMessage.timestamp_ms, CallMessage.created_at)
        )
        return list(messages)


async def add_message(
    session_factory: AsyncSessionMaker,
    call_id: UUID,
    role: MessageRole,
    timestamp_ms: int,
    content: str | None = None,
    tool_calls: list[dict[str, Any]] | None = None,
    tool_call_id: str | None = None,
    tool_name: str | None = None,
) -> None:
    async with session_factory() as session:
        session.add(
            CallMessage(
                call_id=call_id,
                role=role,
                content=content,
                tool_calls=tool_calls,
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                timestamp_ms=timestamp_ms,
            )
        )
        await session.commit()


async def finish_call(
    session_factory: AsyncSessionMaker,
    call_id: UUID,
    status: CallStatus,
    recording_url: str | None = None,
) -> None:
    async with session_factory() as session:
        call = await session.get(Call, call_id)
        if call is None:
            return
        ended_at = get_utc_now()
        call.status = status
        call.recording_url = recording_url
        call.ended_at = ended_at
        call.duration = int((ended_at - call.started_at).total_seconds())
        await session.commit()
