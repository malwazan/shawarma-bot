"""Connects LiveKit rooms to the voice agent.

For each call, the bridge holds a websocket to the voice agent's
`/api/v1/voice/livekit/call/connect` (through HAProxy, which picks a free voice
worker). The open socket is the call's lifecycle signal:

- Caller joins the room  -> open the socket and send the init message; the
                            agent joins the room and runs the pipeline.
- Room finishes          -> close the socket; the agent ends the pipeline.
- Agent closes the socket -> the pipeline ended (caller left, idle timeout,
                            error); delete the room so the caller is
                            disconnected too, instead of waiting alone.

State is in memory, so this must run in a single process (the api service).
"""

import asyncio
import json

import logfire as logger
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

from src.config import settings

from . import service

# One task per room with a running agent, keyed by room name. Also keeps a
# reference to each task, so it isn't garbage-collected mid-call.
_active_agents: dict[str, asyncio.Task[None]] = {}

# The voice workers handle one call each; HAProxy queues extra calls for up to
# 30s (`timeout queue`), so wait a bit longer than that for the handshake.
AGENT_CONNECT_TIMEOUT_SECS = 35


def start_agent(room_name: str, room_metadata: str) -> None:
    """Start the agent for a room, unless one is already running."""
    if room_name in _active_agents:
        logger.info("Agent already running for room - ignoring.", room=room_name)
        return

    _active_agents[room_name] = asyncio.create_task(
        _run_agent_connection(room_name, room_metadata)
    )
    logger.info("Agent connection started.", room=room_name)


def stop_agent(room_name: str) -> None:
    """Close the room's agent connection, which ends its pipeline."""
    task = _active_agents.pop(room_name, None)
    if task is not None:
        task.cancel()
        logger.info("Agent connection stopped (room finished).", room=room_name)


async def _run_agent_connection(room_name: str, room_metadata: str) -> None:
    try:
        async with connect(
            settings.VOICE_AGENT_WS_URL, open_timeout=AGENT_CONNECT_TIMEOUT_SECS
        ) as ws:
            await ws.send(
                json.dumps(
                    {
                        "room_name": room_name,
                        "livekit_token": service.generate_agent_token(room_name),
                        "room_metadata": room_metadata,
                    }
                )
            )
            logger.info("Connected to voice agent.", room=room_name)

            # The agent sends nothing; this returns when it closes the socket.
            async for _ in ws:
                pass
            logger.info("Voice agent ended the call.", room=room_name)

    except asyncio.CancelledError:
        # stop_agent(): the room is already finished. Leaving `async with`
        # closed the socket, which tells the agent to end the pipeline.
        raise

    except ConnectionClosed as exc:
        logger.warning("Voice agent connection dropped.", room=room_name, exc=str(exc))

    except Exception:
        # Includes: no voice worker free in time (HAProxy 503), agent unreachable.
        logger.exception("Couldn't run the voice agent for room.", room=room_name)

    finally:
        _active_agents.pop(room_name, None)

    # Reached only when the call ended from the agent's side (or never started).
    await _end_room(room_name)


async def _end_room(room_name: str) -> None:
    try:
        await service.delete_room(room_name)
    except Exception:
        logger.exception("Failed to delete LiveKit room.", room=room_name)
