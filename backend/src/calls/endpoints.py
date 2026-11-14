from uuid import UUID

from botocore.exceptions import ClientError
from fastapi import APIRouter, Header, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from wireup import Injected

from src.core import storage
from src.user.dependencies import CurrentUser

from . import repository
from .schemas import CallDetailsResponse, CallMessageResponse, CallResponse

router = APIRouter(tags=["Calls"])


@router.get("")
async def list_calls(
    user: CurrentUser, db: Injected[AsyncSession]
) -> list[CallResponse]:
    calls = await repository.list_calls(db, user.id)
    return [CallResponse.model_validate(c) for c in calls]


@router.get("/{call_id}")
async def get_call(
    call_id: UUID, user: CurrentUser, db: Injected[AsyncSession]
) -> CallDetailsResponse:
    call = await repository.get_call(db, user.id, call_id)
    if call is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Call not found")
    messages = await repository.list_messages(db, call_id)
    return CallDetailsResponse(
        **CallResponse.model_validate(call).model_dump(),
        recording_url=(
            f"/api/v1/calls/{call_id}/recording" if call.recording_url else None
        ),
        transcript=[CallMessageResponse.model_validate(m) for m in messages],
    )


@router.get("/{call_id}/recording")
async def stream_call_recording(
    call_id: UUID,
    user: CurrentUser,
    db: Injected[AsyncSession],
    range_header: str | None = Header(None, alias="Range", include_in_schema=False),
) -> StreamingResponse:
    call = await repository.get_call(db, user.id, call_id)
    if call is None or call.recording_url is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recording not found")

    try:
        stream = await storage.open_object_stream(call.recording_url, range_header)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        if code in ("404", "NoSuchKey"):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Recording not found")
        if code in ("416", "InvalidRange"):
            raise HTTPException(
                status.HTTP_416_RANGE_NOT_SATISFIABLE, "Range not satisfiable"
            )
        raise

    headers = {
        "Content-Disposition": f'inline; filename="recording-{call_id}.wav"',
        "Accept-Ranges": "bytes",
    }
    if stream.content_range:
        headers["Content-Range"] = stream.content_range
    return StreamingResponse(
        stream.body,
        status_code=206 if stream.content_range else 200,
        media_type=stream.content_type,
        headers=headers,
    )
