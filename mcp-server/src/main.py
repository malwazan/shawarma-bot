"""MCP server for the Half Million voice agent (port 4501).

    uv run uvicorn src.main:app --port 4501

Serves MCP over HTTP at /mcp; every request needs the shared secret (see
auth.py). GET /health is open. Internal only: Caddy doesn't route to it.
"""

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.auth import AUTH_SECRET, AuthMiddleware
from src.tools import register_tools

mcp = FastMCP("Half Million Coffee Shop", on_duplicate="error")


@mcp.custom_route("/health", methods=["GET"])
async def health_check(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy"})


mcp.add_middleware(AuthMiddleware(auth_secret=AUTH_SECRET))

register_tools(mcp)

app = mcp.http_app()
