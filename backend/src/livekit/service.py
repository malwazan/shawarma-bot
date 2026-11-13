"""LiveKit server API: rooms, access tokens and webhook verification."""

from uuid import UUID, uuid4

from livekit.api import (
    AccessToken,
    LiveKitAPI,
    TokenVerifier,
    VideoGrants,
    WebhookEvent,
    WebhookReceiver,
)
from livekit.protocol.room import CreateRoomRequest, DeleteRoomRequest

from src.config import settings
from src.voice.schemas import LiveKitRoomMetadata

# The voice bot's identity in every room.
AGENT_IDENTITY = "shawarma-agent"

# The bot's display name: shown in the room, and stored as the call's to_number.
AGENT_NAME = "Sarjy"

# Close a room nobody joined after this long (e.g. the browser never connected).
ROOM_EMPTY_TIMEOUT_SECS = 60


def _api() -> LiveKitAPI:
    return LiveKitAPI(
        url=settings.LIVEKIT_API_URL,
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET.get_secret_value(),
    )


def _token(identity: str, name: str, room_name: str) -> AccessToken:
    return (
        AccessToken(
            settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET.get_secret_value()
        )
        .with_identity(identity)
        .with_name(name)
        .with_grants(
            VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
    )


def new_room_name(call_id: UUID) -> str:
    return f"call-{call_id}"


def new_call_id() -> UUID:
    return uuid4()


async def create_room(name: str, metadata: LiveKitRoomMetadata) -> None:
    """The metadata travels with the room, so the webhook (and from there the
    voice agent) knows which call it belongs to."""
    async with _api() as api:
        await api.room.create_room(
            CreateRoomRequest(
                name=name,
                metadata=metadata.to_json(),
                empty_timeout=ROOM_EMPTY_TIMEOUT_SECS,
                max_participants=2,
            )
        )


async def delete_room(name: str) -> None:
    """Disconnects everyone still in the room. Fine if the room is already gone."""
    async with _api() as api:
        await api.room.delete_room(DeleteRoomRequest(room=name))


def generate_user_token(room_name: str, user_id: UUID, user_name: str) -> str:
    """JWT for the browser to join the room."""
    return _token(str(user_id), user_name, room_name).to_jwt()


def generate_agent_token(room_name: str) -> str:
    """JWT for the voice bot to join the room."""
    return _token(AGENT_IDENTITY, AGENT_NAME, room_name).to_jwt()


def verify_webhook(body: str, auth_header: str) -> WebhookEvent:
    """Parse a webhook, checking it was signed with our API secret. Raises if not."""
    verifier = TokenVerifier(
        settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET.get_secret_value()
    )
    return WebhookReceiver(verifier).receive(body, auth_header)
