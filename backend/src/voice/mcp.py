"""Tools from the MCP server, for the voice agent's LLM.

Uses Pipecat's MCPClient over streamable HTTP. `load_mcp_tools()` returns a
ToolsSchema whose tools carry their call handlers: put it in the LLMContext and
the LLM can call them, with Pipecat forwarding each call to the MCP server. The
connection closes when the call's pipeline ends.

The server is optional: if it's unreachable, the call goes ahead without tools.
"""

import asyncio

import logfire as logger
from mcp.client.session_group import StreamableHttpParameters
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.services.mcp_service import MCPClient

from src.config import settings

# Don't hold up the call for long if the server is slow or down: the caller is
# already in the room, waiting for the bot.
CONNECT_TIMEOUT_SECS = 5


def create_mcp_client() -> MCPClient:
    return MCPClient(
        server_params=StreamableHttpParameters(
            url=settings.MCP_SERVER_URL,
            headers={
                "Authorization": f"Bearer {settings.MCP_SERVER_SECRET.get_secret_value()}"
            },
            timeout=CONNECT_TIMEOUT_SECS,
        )
    )


async def load_mcp_tools() -> ToolsSchema | None:
    """Connect to the MCP server and list its tools. None if that fails."""
    client = create_mcp_client()
    try:
        tools = await asyncio.wait_for(client.tools(), timeout=CONNECT_TIMEOUT_SECS)
    except Exception as exc:
        logger.warning(
            "MCP server unavailable - the call continues without tools.",
            url=settings.MCP_SERVER_URL,
            error=f"{type(exc).__name__}: {exc}",
        )
        await _close_quietly(client)
        return None

    logger.info(
        "Loaded MCP tools.",
        url=settings.MCP_SERVER_URL,
        tools=[tool.name for tool in tools.standard_tools],
    )
    return tools


async def _close_quietly(client: MCPClient) -> None:
    try:
        await client.close()
    except Exception:
        pass
