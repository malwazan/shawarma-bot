"""Saves a call's transcript to the database while the call is running.

Sources:
- system:    the system prompt, when the call starts
- user:      `on_user_turn_stopped` from the user context aggregator
- assistant: `on_assistant_turn_stopped` from the assistant context aggregator
             (what the bot actually said, cut short if the caller interrupted)
- tool calls and results: FunctionCallsStartedFrame / FunctionCallResultFrame,
             seen by this observer as they pass through the pipeline

Rows are queued and written one at a time by a background task, in order, so
the pipeline never waits on the database.
"""

import asyncio
import json
import time
from typing import Any
from uuid import UUID

import logfire as logger
from pipecat.frames.frames import FunctionCallResultFrame, FunctionCallsStartedFrame
from pipecat.observers.base_observer import BaseObserver, FramePushed
from pipecat.processors.aggregators.llm_response_universal import (
    AssistantTurnStoppedMessage,
    LLMContextAggregatorPair,
    UserTurnStoppedMessage,
)

from src.core.db.session import AsyncSessionMaker
from src.models import MessageRole
from src.voice import repository

# At the end of a call, how long to wait for queued rows to be written.
FLUSH_TIMEOUT_SECS = 5


class TranscriptRecorder(BaseObserver):
    def __init__(
        self,
        call_id: UUID,
        session_factory: AsyncSessionMaker,
        aggregators: LLMContextAggregatorPair,
    ) -> None:
        super().__init__()
        self._call_id = call_id
        self._session_factory = session_factory
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._writer: asyncio.Task[None] | None = None
        self._started_at = time.monotonic()
        # A frame is observed once per hop through the pipeline; record it once.
        self._seen: set[str] = set()

        aggregators.user().add_event_handler("on_user_turn_stopped", self._on_user_turn)
        aggregators.assistant().add_event_handler(
            "on_assistant_turn_stopped", self._on_assistant_turn
        )

    def start(self, system_prompt: str) -> None:
        self._started_at = time.monotonic()
        self._writer = asyncio.create_task(self._write_loop())
        self._record(role=MessageRole.SYSTEM, content=system_prompt)

    async def close(self) -> None:
        """Write what's still queued, then stop the writer."""
        if self._writer is None:
            return
        try:
            await asyncio.wait_for(self._queue.join(), timeout=FLUSH_TIMEOUT_SECS)
        except TimeoutError:
            logger.warning(
                "Transcript: gave up on unsaved messages.",
                call_id=str(self._call_id),
                unsaved=self._queue.qsize(),
            )
        self._writer.cancel()

    # -- Sources --------------------------------------------------------------

    async def _on_user_turn(
        self, _aggregator: object, _strategy: object, message: UserTurnStoppedMessage
    ) -> None:
        if message.content:
            self._record(role=MessageRole.USER, content=message.content)

    async def _on_assistant_turn(
        self, _aggregator: object, message: AssistantTurnStoppedMessage
    ) -> None:
        if message.content:
            self._record(role=MessageRole.ASSISTANT, content=message.content)

    async def on_push_frame(self, data: FramePushed) -> None:
        frame = data.frame

        if isinstance(frame, FunctionCallsStartedFrame):
            calls = [
                c for c in frame.function_calls if self._once(f"call:{c.tool_call_id}")
            ]
            if calls:
                self._record(
                    role=MessageRole.ASSISTANT,
                    tool_calls=[
                        {
                            "id": c.tool_call_id,
                            "name": c.function_name,
                            "arguments": c.arguments,
                        }
                        for c in calls
                    ],
                )

        elif isinstance(frame, FunctionCallResultFrame):
            if self._once(f"result:{frame.tool_call_id}"):
                self._record(
                    role=MessageRole.TOOL,
                    content=_to_text(frame.result),
                    tool_call_id=frame.tool_call_id,
                    tool_name=frame.function_name,
                )

    # -- Writing --------------------------------------------------------------

    def _once(self, key: str) -> bool:
        if key in self._seen:
            return False
        self._seen.add(key)
        return True

    def _record(
        self,
        *,
        role: MessageRole,
        content: str | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
        tool_call_id: str | None = None,
        tool_name: str | None = None,
    ) -> None:
        """Queue a message for the writer, stamped with the time since the call started."""
        self._queue.put_nowait(
            {
                "role": role,
                "content": content,
                "tool_calls": tool_calls,
                "tool_call_id": tool_call_id,
                "tool_name": tool_name,
                "timestamp_ms": int((time.monotonic() - self._started_at) * 1000),
            }
        )

    async def _write_loop(self) -> None:
        while True:
            message = await self._queue.get()
            try:
                await repository.add_message(
                    self._session_factory, self._call_id, **message
                )
            except Exception:
                # A lost transcript line must never break the call.
                logger.exception(
                    "Transcript: failed to save a message.",
                    call_id=str(self._call_id),
                    role=str(message.get("role")),
                )
            finally:
                self._queue.task_done()


def _to_text(result: object) -> str | None:
    if result is None or isinstance(result, str):
        return result
    try:
        return json.dumps(result, default=str)
    except TypeError:
        return str(result)
