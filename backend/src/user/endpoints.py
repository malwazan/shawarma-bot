from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool
from wireup import Injected

from src.models import User

from . import keys, repository
from .cookies import clear_session_token, get_session_token, set_session_token
from .dependencies import CurrentUser
from .keys import ApiKeys, mask
from .schemas import (
    ApiKeysResponse,
    ApiKeysUpdate,
    FactsResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from .security import DUMMY_PASSWORD_HASH, hash_password, verify_password

router = APIRouter(tags=["Users"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    response: Response,
    db: Injected[AsyncSession],
) -> UserResponse:
    user = User(
        name=body.name, password=await run_in_threadpool(hash_password, body.password)
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Name is already taken")

    session = await repository.create_session(db, user)
    await db.commit()

    set_session_token(response, session.token)
    return UserResponse.model_validate(user)


@router.post("/login")
async def login(
    body: LoginRequest,
    response: Response,
    db: Injected[AsyncSession],
) -> UserResponse:
    user = await repository.get_user_by_name(db, body.name)
    password_hash = user.password if user else DUMMY_PASSWORD_HASH
    valid = await run_in_threadpool(verify_password, body.password, password_hash)
    if user is None or not valid:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid name or password")

    session = await repository.create_session(db, user)
    await db.commit()

    set_session_token(response, session.token)
    return UserResponse.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    db: Injected[AsyncSession],
) -> None:
    if token := get_session_token(request):
        await repository.delete_session(db, token)
        await db.commit()
    clear_session_token(response)


@router.get("/session")
async def get_session(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)


@router.get("/facts")
async def get_facts(user: CurrentUser) -> FactsResponse:
    """What the bot has learned about the user from their calls."""
    lines = (user.facts or "").splitlines()
    return FactsResponse(
        facts=[line.removeprefix("- ").strip() for line in lines if line.strip()]
    )


@router.delete("/facts", status_code=status.HTTP_204_NO_CONTENT)
async def clear_facts(user: CurrentUser, db: Injected[AsyncSession]) -> None:
    """Make the bot forget everything it learned about the user."""
    await db.execute(update(User).where(User.id == user.id).values(facts=None))
    await db.commit()


def _masked(keys: ApiKeys) -> ApiKeysResponse:
    return ApiKeysResponse(
        llm_key=mask(keys.llm_key),
        stt_key=mask(keys.stt_key),
        tts_key=mask(keys.tts_key),
    )


@router.get("/api-keys")
async def get_api_keys(
    user: CurrentUser, db: Injected[AsyncSession]
) -> ApiKeysResponse:
    """The user's keys for the voice bot, masked."""
    return _masked(await keys.get_keys(db, user.id))


@router.put("/api-keys")
async def update_api_keys(
    body: ApiKeysUpdate, user: CurrentUser, db: Injected[AsyncSession]
) -> ApiKeysResponse:
    """Set some or all keys; the ones left out keep their saved value."""
    changes = body.model_dump(exclude_none=True)
    updated = await keys.update_keys(db, user.id, changes)
    await db.commit()
    return _masked(updated)
