import asyncio
from collections.abc import Coroutine
from typing import Any

import logfire as logger

# Strong references to running background tasks: asyncio only keeps weak ones,
# so an unreferenced task can be garbage-collected before it finishes.
_background_tasks: set[asyncio.Task[None]] = set()


def run_in_background(coro: Coroutine[Any, Any, None], name: str) -> None:
    """Run `coro` without waiting for it. Its errors are logged, not raised."""

    async def run() -> None:
        try:
            await coro
        except Exception:
            logger.exception("Background task failed.", task=name)

    task = asyncio.create_task(run(), name=name)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
