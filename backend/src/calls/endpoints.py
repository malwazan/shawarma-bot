from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from wireup import Injected

from src.user.dependencies import CurrentUser

from . import repository
from .schemas import CallMessageResponse, CallResponse

router = APIRouter(tags=["Calls"])


@router.get("")
async def list_calls(
    user: CurrentUser, db: Injected[AsyncSession]
) -> list[CallResponse]:
    """The current user's most recent calls, newest first."""
    calls = await repository.list_calls(db, user.id)
    return [CallResponse.model_validate(c) for c in calls]


@router.get("/{call_id}/messages")
async def list_call_messages(
    call_id: UUID, user: CurrentUser, db: Injected[AsyncSession]
) -> list[CallMessageResponse]:
    """A call's transcript so far, oldest first. Grows while the call is live."""
    if await repository.get_call(db, user.id, call_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Call not found")
    messages = await repository.list_messages(db, call_id)
    return [CallMessageResponse.model_validate(m) for m in messages]
