import asyncio

import logfire as logger
from fastapi import WebSocket
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import EndFrame, ErrorFrame, LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import (
    PipelineParams,
    PipelineWorker,
    ProcessorUnusablePolicy,
)
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.transports.livekit.transport import LiveKitParams, LiveKitTransport
from pipecat.workers.runner import WorkerRunner

from src.config import settings
from src.core.background import run_in_background
from src.core.db.session import AsyncSessionMaker
from src.models import CallStatus
from src.user.keys import ApiKeys
from src.voice import repository
from src.voice.facts import update_user_facts
from src.voice.mcp import load_mcp_tools
from src.voice.prompt import build_prompt
from src.voice.providers import create_llm, create_stt, create_tts
from src.voice.schemas import CallMetadata, LiveKitAgentInit
from src.voice.transcript import TranscriptRecorder

# Once the websocket closes, how long the pipeline gets to finish speaking and
# shut down before it is cancelled.
END_TIMEOUT_SECS = 30


class VoiceService:
    def __init__(self, session_factory: AsyncSessionMaker) -> None:
        self._session_factory = session_factory

    async def start(
        self,
        websocket: WebSocket,
        init: LiveKitAgentInit,
        call_metadata: CallMetadata,
    ) -> None:
        call_id = call_metadata.call_id

        # The services run on the calling user's own keys. The api checked
        # they're set when the call was created; re-check in case they changed.
        keys = await repository.get_keys_for_call(self._session_factory, call_id)
        facts = await repository.get_facts_for_call(self._session_factory, call_id)

        failed = False
        try:
            if keys.missing():
                logger.error(
                    "Call has missing API keys - not starting the bot.",
                    call_id=str(call_id),
                    missing=keys.missing(),
                )
                failed = True
            else:
                failed = not await self._run_call(
                    websocket, init, call_metadata, keys, facts
                )
        except BaseException:
            failed = True
            raise
        finally:
            # Unconditional: overrides the room_finished webhook's fallback if
            # that arrived first.
            status = CallStatus.FAILED if failed else CallStatus.COMPLETED
            try:
                await repository.finish_call(self._session_factory, call_id, status)
                logger.info("Call finished.", call_id=str(call_id), status=status.value)
            except Exception:
                logger.exception(
                    "Failed to save the call's final status.", call_id=str(call_id)
                )

            # Learn about the caller from this call, in the background: the
            # caller has already hung up, and the bridge needn't wait for it.
            # Also after a failed call: whatever the caller said still counts.
            if keys.llm_key:
                run_in_background(
                    update_user_facts(self._session_factory, call_id, keys.llm_key),
                    name=f"facts:{call_id}",
                )

    async def _run_call(
        self,
        websocket: WebSocket,
        init: LiveKitAgentInit,
        call_metadata: CallMetadata,
        keys: ApiKeys,
        facts: str | None,
    ) -> bool:
        """Run the call. Returns False if it failed (a provider stopped working)."""
        assert keys.llm_key and keys.stt_key and keys.tts_key

        transport = self._create_transport(init)

        system_prompt = build_prompt(facts)
        stt = create_stt(keys.stt_key)
        llm = create_llm(keys.llm_key, system_prompt)
        tts = create_tts(keys.tts_key)

        # The MCP tools carry their handlers: listing them in the context is
        # enough for the LLM to call them.
        tools = await load_mcp_tools()
        context = LLMContext(tools=tools) if tools is not None else LLMContext()
        aggregators = LLMContextAggregatorPair(
            context,
            user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer()),
        )
        transcript = TranscriptRecorder(
            call_metadata.call_id, self._session_factory, aggregators
        )

        pipeline = Pipeline(
            [
                transport.input(),
                stt,
                aggregators.user(),
                llm,
                tts,
                transport.output(),
                aggregators.assistant(),
            ]
        )

        worker = PipelineWorker(
            pipeline,
            conversation_id=str(call_metadata.call_id),
            enable_tracing=True,
            idle_timeout_secs=60 * 3,
            # No fallback providers: if STT, LLM or TTS fails for good (bad API
            # key, outage), end the call instead of leaving the caller with a
            # silent bot. The bridge then closes the room, and the browser.
            processor_unusable_policy=ProcessorUnusablePolicy.END,
            params=PipelineParams(enable_metrics=True, enable_usage_metrics=True),
            observers=[transcript],
        )

        self._register_event_handlers(transport, worker)

        failed = False

        @worker.event_handler("on_pipeline_error")
        async def on_pipeline_error(_worker: PipelineWorker, frame: ErrorFrame) -> None:
            # Errors a call can't recover from: a fatal error, or a processor
            # (STT/LLM/TTS) that can no longer work, which ends the call.
            nonlocal failed
            if frame.fatal or (frame.processor and not frame.processor.is_usable):
                failed = True

        # handle_sigint=False: uvicorn owns Ctrl+C. force_gc=True: free the
        # pipeline's memory once the call ends, since this process keeps running.
        runner = WorkerRunner(handle_sigint=False, force_gc=True)

        with logger.set_baggage(
            **{
                "call.id": str(call_metadata.call_id),
                "call.from": call_metadata.from_,
                "call.to": call_metadata.to,
            }
        ):
            transcript.start(system_prompt)
            try:
                await self._run(runner, worker, websocket)
            finally:
                await transcript.close()

        return not failed

    @staticmethod
    def _create_transport(init: LiveKitAgentInit) -> LiveKitTransport:
        url = settings.LIVEKIT_API_URL.replace("http", "ws", 1)
        return LiveKitTransport(
            url=url,
            token=init.livekit_token,
            room_name=init.room_name,
            params=LiveKitParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                video_in_enabled=False,
                video_out_enabled=False,
            ),
        )

    @staticmethod
    def _register_event_handlers(
        transport: LiveKitTransport, worker: PipelineWorker
    ) -> None:
        @transport.event_handler("on_first_participant_joined")
        async def on_first_participant_joined(
            _transport: LiveKitTransport, participant_id: str
        ) -> None:
            logger.info("Caller joined the room.", participant_id=participant_id)
            # Run the LLM on the system prompt alone, so the bot speaks first.
            await worker.queue_frame(LLMRunFrame())

        @transport.event_handler("on_participant_disconnected")
        async def on_participant_disconnected(
            _transport: LiveKitTransport, participant_id: str
        ) -> None:
            logger.info("Caller left the room.", participant_id=participant_id)
            # Nobody is listening any more, so stop right away.
            await worker.cancel()

    @staticmethod
    async def _run(
        runner: WorkerRunner, worker: PipelineWorker, websocket: WebSocket
    ) -> None:
        """Run the pipeline while watching the websocket; whichever ends first
        ends the other:

        - Pipeline ends (caller left, idle timeout, error): return or raise, and
          the endpoint closes the websocket.
        - Websocket closes (the room was closed): send EndFrame so the bot
          finishes what it's saying, then cancel if it takes too long.
        """
        await runner.add_workers(worker)
        pipeline_task = asyncio.create_task(runner.run())
        ws_task = asyncio.create_task(_wait_for_disconnect(websocket))

        try:
            done, _ = await asyncio.wait(
                {pipeline_task, ws_task}, return_when=asyncio.FIRST_COMPLETED
            )

            if pipeline_task in done:
                await pipeline_task  # re-raise if the pipeline failed
                return

            logger.info("Websocket closed - ending the pipeline.")
            await worker.queue_frame(EndFrame())
            try:
                # Cancels the pipeline on timeout.
                await asyncio.wait_for(pipeline_task, timeout=END_TIMEOUT_SECS)
            except TimeoutError:
                logger.warning("Pipeline did not end in time - cancelled it.")
        finally:
            # No-op for finished tasks; cleans up if this coroutine is cancelled.
            ws_task.cancel()
            pipeline_task.cancel()


async def _wait_for_disconnect(websocket: WebSocket) -> None:
    """Return once the other side closes the websocket. Other messages are ignored."""
    while True:
        message = await websocket.receive()
        if message["type"] == "websocket.disconnect":
            return
