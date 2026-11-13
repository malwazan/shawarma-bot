import logfire as logger
from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from wireup import Injected

from src.calls import repository as calls_repository
from src.config import settings
from src.database import MainDatabase
from src.user import keys as user_keys
from src.user.dependencies import CurrentUser
from src.voice.schemas import LiveKitRoomMetadata

from . import bridge, service
from .schemas import CallCreateResponse

router = APIRouter(tags=["LiveKit"])


@router.post("/calls", status_code=status.HTTP_201_CREATED)
async def create_call(
    user: CurrentUser, db: Injected[AsyncSession]
) -> CallCreateResponse:
    """Create a call: its row (in_progress) and its LiveKit room. The browser
    joins the room with the returned token; the webhook below then brings the
    voice agent in.
    """

    missing = (await user_keys.get_keys(db, user.id)).missing()
    if missing:
        raise HTTPException(
            status.HTTP_412_PRECONDITION_FAILED,
            f"Add your {', '.join(missing)} API key{'s' if len(missing) > 1 else ''} "
            "in your profile before making a call.",
        )

    call_id = service.new_call_id()
    room_name = service.new_room_name(call_id)

    try:
        await service.create_room(
            room_name,
            LiveKitRoomMetadata(
                call_id=call_id, from_=user.name, to=service.AGENT_NAME
            ),
        )
    except Exception:
        logger.exception("Failed to create LiveKit room.", room=room_name)
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Couldn't start the call. Try again."
        )

    # After the room, so a failed room leaves no call row behind. The browser
    # only gets the token below, so no webhook can arrive before this commit.
    await calls_repository.create_call(db, call_id, user, to_number=service.AGENT_NAME)
    await db.commit()

    logger.info("Call created.", room=room_name, call_id=str(call_id))
    return CallCreateResponse(
        call_id=call_id,
        room_name=room_name,
        token=service.generate_user_token(room_name, user.id, user.name),
        livekit_url=settings.LIVEKIT_URL,
    )


@router.post("/webhook", include_in_schema=False)
async def livekit_webhook(
    request: Request, db: Injected[MainDatabase]
) -> dict[str, str]:
    """Called by the LiveKit server (see docker/livekit/config*.yaml) on room
    and participant events. Acts as the bridge to the voice agent.
    """

    body = (await request.body()).decode()
    try:
        event = service.verify_webhook(body, request.headers.get("Authorization", ""))
    except Exception:
        logger.warning("Rejected LiveKit webhook with an invalid signature.")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid signature")

    room = event.room if event.HasField("room") else None
    participant = event.participant if event.HasField("participant") else None
    logger.info(
        "LiveKit webhook.",
        lk_event=event.event,
        room=room.name if room else None,
        participant=participant.identity if participant else None,
    )

    if event.event == "participant_joined" and room and participant:
        if participant.identity == service.AGENT_IDENTITY:
            pass  # the bot itself joining
        elif not room.metadata:
            logger.warning(
                "Room has no call metadata - not starting the agent.", room=room.name
            )
        else:
            bridge.start_agent(room.name, room.metadata)

    elif event.event == "room_finished" and room:
        bridge.stop_agent(room.name)
        # Normally the voice agent has already finished the call. If it never
        # ran (caller never joined, no voice worker free) or crashed before
        # finishing, the call would stay in_progress forever: mark it failed.
        if room.metadata:
            metadata = LiveKitRoomMetadata.from_json(room.metadata)
            await calls_repository.fail_call_if_unfinished(
                db.session_factory, metadata.call_id
            )

    return {"status": "ok"}
