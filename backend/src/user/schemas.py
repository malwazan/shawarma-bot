from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

Name = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=256)
]
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]


class RegisterRequest(BaseModel):
    name: Name
    password: Password


class LoginRequest(BaseModel):
    name: Name
    password: Annotated[str, StringConstraints(max_length=128)]


ApiKey = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=512)
]


class ApiKeysResponse(BaseModel):
    """Masked keys ("••••abcd"), or null if not set. Saved keys never leave the server."""

    llm_key: str | None
    stt_key: str | None
    tts_key: str | None


class ApiKeysUpdate(BaseModel):
    """Keys to set. Omitted (or null) keys keep their saved value."""

    llm_key: ApiKey | None = None
    stt_key: ApiKey | None = None
    tts_key: ApiKey | None = None


class FactsResponse(BaseModel):
    """What the bot remembers about the user, one fact per item."""

    facts: list[str]


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    created_at: datetime
