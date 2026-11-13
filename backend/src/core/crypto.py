"""Encryption for secrets stored in the database (users' API keys).

Fernet (AES-128-CBC + HMAC-SHA256) with a key derived from AUTH_SECRET, so a
database dump alone doesn't reveal the keys. Changing AUTH_SECRET makes stored
values unreadable: decrypt() then returns None, and users re-enter their keys.
"""

import base64
import hashlib
from functools import cache

from cryptography.fernet import Fernet, InvalidToken

from src.config import settings


@cache
def _fernet() -> Fernet:
    # Domain-separated from AUTH_SECRET's other use (signing session cookies).
    digest = hashlib.sha256(
        b"shawarma-bot:user-keys:" + settings.AUTH_SECRET.get_secret_value().encode()
    ).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str | None:
    """The plaintext, or None if it can't be decrypted (e.g. AUTH_SECRET changed)."""
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        return None
