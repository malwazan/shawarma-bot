from uuid import UUID

from pydantic import BaseModel


class CallCreateResponse(BaseModel):
    """What the browser needs to join the call's LiveKit room."""

    call_id: UUID
    room_name: str
    token: str
    livekit_url: str
