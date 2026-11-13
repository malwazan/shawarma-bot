from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.utils import get_utc_now
from src.models import Session, User

from .cookies import SESSION_MAX_AGE
from .security import generate_session_token


async def get_user_by_name(db: AsyncSession, name: str) -> User | None:
    return await db.scalar(select(User).where(User.name == name))


async def get_user_by_session_token(db: AsyncSession, token: str) -> User | None:
    """The session's user, or None if the token is unknown or expired."""
    return await db.scalar(
        select(User)
        .join(Session, Session.user_id == User.id)
        .where(Session.token == token, Session.expires_at > get_utc_now())
    )


async def create_session(db: AsyncSession, user: User) -> Session:
    session = Session(
        user_id=user.id,
        token=generate_session_token(),
        expires_at=get_utc_now() + SESSION_MAX_AGE,
    )
    db.add(session)
    await db.flush()
    return session


async def delete_session(db: AsyncSession, token: str) -> None:
    await db.execute(delete(Session).where(Session.token == token))
