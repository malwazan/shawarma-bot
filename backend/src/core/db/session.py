from collections.abc import AsyncGenerator
from typing import Any, TypeAlias

import orjson
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import DatabaseSettings

AsyncSessionMaker: TypeAlias = async_sessionmaker[AsyncSession]


def orjson_serializer(obj: Any) -> str:  # noqa: ANN401
    return orjson.dumps(obj).decode("utf-8")


def orjson_deserializer(json_string: str) -> Any:  # noqa: ANN401
    return orjson.loads(json_string)


async def create_database_engine(
    db_settings: DatabaseSettings,
    debug: bool = False,
) -> AsyncGenerator[AsyncEngine]:
    engine = create_async_engine(
        db_settings.dsn,
        pool_size=db_settings.pool_size,
        pool_recycle=db_settings.pool_recycle_seconds,
        pool_pre_ping=db_settings.pool_pre_ping,
        echo=debug,
        json_serializer=orjson_serializer,
        json_deserializer=orjson_deserializer,
    )

    try:
        yield engine
    finally:
        await engine.dispose()


def create_session_factory(
    engine: AsyncEngine,
) -> AsyncSessionMaker:
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
