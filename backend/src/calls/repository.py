"""Call and transcript storage. The call's lifecycle:

1. create_call()           POST /livekit/calls          -> in_progress
2. add_message()           voice agent, during the call -> transcript rows
3. finish_call()           voice agent, when it ends    -> completed / failed
   (2 and 3 are in src/voice/repository.py)
4. fail_call_if_unfinished()  room_finished webhook     -> failed, only if the
   agent never finished it (it never started, or crashed before finishing)
"""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.session import AsyncSessionMaker
from src.core.utils import get_utc_now
from src.models import Call, CallMessage, CallStatus, User


async def create_call(
    session: AsyncSession, call_id: UUID, user: User, to_number: str
) -> Call:
    call = Call(
        id=call_id,
        user_id=user.id,
        from_number=user.name,
        to_number=to_number,
        status=CallStatus.IN_PROGRESS,
        started_at=get_utc_now(),
    )
    session.add(call)
    await session.flush()
    return call


async def fail_call_if_unfinished(
    session_factory: AsyncSessionMaker, call_id: UUID
) -> None:
    ended_at = get_utc_now()
    async with session_factory() as session:
        await session.execute(
            update(Call)
            .where(Call.id == call_id, Call.status == CallStatus.IN_PROGRESS)
            .values(
                status=CallStatus.FAILED,
                ended_at=ended_at,
                duration=0,
            )
        )
        await session.commit()


async def list_calls(
    session: AsyncSession, user_id: UUID, limit: int = 50
) -> list[Call]:
    result = await session.scalars(
        select(Call)
        .where(Call.user_id == user_id)
        .order_by(Call.started_at.desc())
        .limit(limit)
    )
    return list(result)


async def get_call(session: AsyncSession, user_id: UUID, call_id: UUID) -> Call | None:
    return await session.scalar(
        select(Call).where(Call.id == call_id, Call.user_id == user_id)
    )


async def list_messages(session: AsyncSession, call_id: UUID) -> list[CallMessage]:
    result = await session.scalars(
        select(CallMessage)
        .where(CallMessage.call_id == call_id)
        .order_by(CallMessage.timestamp_ms, CallMessage.created_at)
    )
    return list(result)
