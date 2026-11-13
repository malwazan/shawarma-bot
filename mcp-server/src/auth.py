import hmac
from typing import Any

from fastmcp.exceptions import FastMCPError
from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import Middleware, MiddlewareContext

# Must match MCP_SERVER_SECRET in backend/src/config.py.
AUTH_SECRET = "dev-mcp-secret"


class AuthMiddleware(Middleware):
    """Rejects MCP requests without `Authorization: Bearer <AUTH_SECRET>`."""

    def __init__(self, auth_secret: str) -> None:
        self.expected = f"Bearer {auth_secret}"

    async def on_request(self, context: MiddlewareContext, call_next: Any) -> Any:  # noqa: ANN401
        # include_all: get_http_headers() leaves out Authorization by default.
        headers = get_http_headers(include_all=True) or {}
        if not hmac.compare_digest(headers.get("authorization", ""), self.expected):
            raise FastMCPError("Unauthorized: missing or invalid token")
        return await call_next(context)
