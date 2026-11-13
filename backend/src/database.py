from collections.abc import AsyncIterator
from contextlib import aclosing
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
)
from wireup import injectable

from src.config import settings
from src.core.db.session import (
    AsyncSessionMaker,
    create_database_engine,
    create_session_factory,
)
from src.logfire import instrument_sqlalchemy


@dataclass(frozen=True)
class MainDatabase:
    engine: AsyncEngine
    session_factory: AsyncSessionMaker


@injectable
async def provide_main_database() -> AsyncIterator[MainDatabase]:
    async with aclosing(
        create_database_engine(
            db_settings=settings.main_db_settings,
            debug=settings.DEBUG,
        )
    ) as engine_generator:
        engine = await anext(engine_generator)
        instrument_sqlalchemy(engine)

        yield MainDatabase(
            engine=engine,
            session_factory=create_session_factory(engine),
        )


@injectable(lifetime="scoped")
async def provide_db_session(db: MainDatabase) -> AsyncIterator[AsyncSession]:
    """One session per request. Endpoints commit explicitly; anything uncommitted
    is rolled back when the session closes."""
    async with db.session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
