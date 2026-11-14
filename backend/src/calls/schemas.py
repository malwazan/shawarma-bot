from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.models import CallStatus, MessageRole


class CallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    from_number: str
    to_number: str
    duration: int | None
    status: CallStatus
    started_at: datetime
    ended_at: datetime | None


class CallMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: MessageRole
    content: str | None
    tool_calls: list[dict[str, Any]] | None
    tool_call_id: str | None
    tool_name: str | None
    timestamp_ms: int


class CallDetailsResponse(CallResponse):
    recording_url: (
        str | None
    )  # presigned link to the recording; None until the call ends
    transcript: list[CallMessageResponse]
