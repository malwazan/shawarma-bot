"""Users' own API keys for the voice bot (LLM, STT, TTS), encrypted at rest."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.crypto import decrypt, encrypt
from src.models import UserKeys

# What each key is for, in the words used in errors shown to the user.
KEY_LABELS = {
    "llm_key": "LLM",
    "stt_key": "Speech to Text",
    "tts_key": "Text to Speech",
}


@dataclass(frozen=True)
class ApiKeys:
    """Decrypted keys. None = not set (or no longer readable)."""

    llm_key: str | None = None
    stt_key: str | None = None
    tts_key: str | None = None

    def missing(self) -> list[str]:
        """Labels of the keys that aren't set, e.g. ["LLM", "Text to Speech"]."""
        return [
            label for field, label in KEY_LABELS.items() if not getattr(self, field)
        ]


def mask(key: str | None) -> str | None:
    """Enough to recognise a saved key without revealing it: "••••abcd"."""
    if not key:
        return None
    return "••••" + key[-4:] if len(key) > 8 else "••••"


def decrypt_keys(row: UserKeys | None) -> ApiKeys:
    if row is None:
        return ApiKeys()
    return ApiKeys(
        **{
            field: decrypt(value) if (value := getattr(row, field)) else None
            for field in KEY_LABELS
        }
    )


async def get_keys(db: AsyncSession, user_id: UUID) -> ApiKeys:
    row = await db.scalar(select(UserKeys).where(UserKeys.user_id == user_id))
    return decrypt_keys(row)


async def update_keys(
    db: AsyncSession, user_id: UUID, changes: dict[str, str]
) -> ApiKeys:
    """Set the given keys (field -> plaintext); keys not given are left as they are."""
    row = await db.scalar(select(UserKeys).where(UserKeys.user_id == user_id))
    if row is None:
        row = UserKeys(user_id=user_id)
        db.add(row)
    for field, value in changes.items():
        setattr(row, field, encrypt(value))
    await db.flush()
    return decrypt_keys(row)
