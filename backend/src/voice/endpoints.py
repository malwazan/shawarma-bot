import logfire as logger
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from wireup import Injected

from src.database import MainDatabase
from src.voice.schemas import CallMetadata, LiveKitAgentInit

from .service import VoiceService

router = APIRouter(tags=["Voice"])


@router.websocket("/livekit/call/connect")
async def start_call(websocket: WebSocket, db: Injected[MainDatabase]) -> None:
    await websocket.accept()

    try:
        raw = await websocket.receive_json()
    except WebSocketDisconnect, Exception:
        logger.warning("LiveKit agent WS closed before init message received.")
        return

    try:
        init = LiveKitAgentInit.model_validate(raw)
    except Exception:
        logger.exception("Invalid LiveKitAgentInit message received.")
        await websocket.close(code=1008)
        return

    try:
        room_metadata = init.parse_room_metadata()
    except Exception:
        logger.exception("Failed to parse room_metadata in LiveKitAgentInit.")
        await websocket.close(code=1008)
        return

    logger.info(
        "LiveKit agent WS connected.",
        room=init.room_name,
        call_id=str(room_metadata.call_id),
    )

    call_metadata = CallMetadata(
        call_id=room_metadata.call_id,
        from_=room_metadata.from_,
        to=room_metadata.to,
    )

    try:
        service = VoiceService(db.session_factory)
        await service.start(websocket, init, call_metadata)
    except Exception:
        logger.exception(
            "Unhandled error in LiveKit call pipeline.",
            room=init.room_name,
            call_id=str(room_metadata.call_id),
        )
    finally:
        # Safety net to close websocket even if call service raises exception
        try:
            await websocket.close()
        except Exception:
            pass

    logger.info(
        "LiveKit agent WS call finished.",
        room=init.room_name,
        call_id=str(room_metadata.call_id),
    )
