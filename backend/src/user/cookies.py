"""Signed, HttpOnly session cookie.

The cookie value is `{token}.{base64(HMAC-SHA256(secret, token))}`, URL-quoted.
A cookie whose signature does not verify is treated as absent.
"""

import base64
import hashlib
import hmac
from datetime import timedelta
from urllib.parse import quote, unquote

from fastapi import Request, Response

from src.config import settings

SESSION_MAX_AGE = timedelta(days=7)

_COOKIE_NAME = (
    "__Secure-shawarma-auth.session_token"
    if settings.COOKIE_SECURE
    else "shawarma-auth.session_token"
)


def _signature(value: str) -> str:
    secret = settings.AUTH_SECRET.get_secret_value().encode()
    digest = hmac.new(secret, value.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


def _sign(value: str) -> str:
    return quote(f"{value}.{_signature(value)}", safe="")


def _unsign(raw: str) -> str | None:
    value, sep, signature = unquote(raw).rpartition(".")
    if not sep or not value:
        return None
    return value if hmac.compare_digest(signature, _signature(value)) else None


def _set(response: Response, value: str, max_age: int) -> None:
    response.set_cookie(
        key=_COOKIE_NAME,
        value=value,
        max_age=max_age,
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
    )


def get_session_token(request: Request) -> str | None:
    raw = request.cookies.get(_COOKIE_NAME)
    return _unsign(raw) if raw else None


def set_session_token(response: Response, token: str) -> None:
    _set(response, _sign(token), int(SESSION_MAX_AGE.total_seconds()))


def clear_session_token(response: Response) -> None:
    _set(response, "", 0)
