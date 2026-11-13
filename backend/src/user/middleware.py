from fastapi import Request
from starlette.types import ASGIApp, Receive, Scope, Send
from wireup.integration.fastapi import get_app_container

from src.database import MainDatabase

from .cookies import get_session_token
from .repository import get_user_by_session_token


class AuthMiddleware:
    """Resolves the session cookie into `request.state.user` (a User, or None).

    It never rejects a request: endpoints that need a logged-in user declare
    the `CurrentUser` dependency, which raises 401 when the user is None.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        user = None
        token = get_session_token(Request(scope))
        if token:
            db = await get_app_container(scope["app"]).get(MainDatabase)
            async with db.session_factory() as session:
                user = await get_user_by_session_token(session, token)

        scope.setdefault("state", {})["user"] = user
        await self.app(scope, receive, send)
