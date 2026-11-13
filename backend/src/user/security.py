"""Password hashing and session tokens.

Hashing (better-auth compatible scrypt):
    format  {salt_hex}:{key_hex}
    salt    16 random bytes, hex-encoded; scrypt receives the hex string's UTF-8 bytes
    input   NFKC-normalised password
"""

import hashlib
import hmac
import os
import unicodedata
import uuid

_SCRYPT_N = 16384
_SCRYPT_R = 16
_SCRYPT_P = 1
_SCRYPT_DKLEN = 64
_SCRYPT_MAXMEM = 64 * 1024 * 1024

# Hash of a throw-away password. Login verifies against it when the user does not
# exist, so the response takes as long as a real check (no user enumeration by timing).
DUMMY_PASSWORD_HASH = "5f3a9c1e7b2d4a6c8e0f1a2b3c4d5e6f:e3577647b3d355988f7cf2a41f887ea9c7273c51b3831615a3a053f70698147ef2824ea26321383dbb5db6a1ddf35f45c552edce83deac7ffc479f7b922611aa"


def _scrypt(password: str, salt_hex: str) -> str:
    normalized = unicodedata.normalize("NFKC", password).encode("utf-8")
    key = hashlib.scrypt(
        normalized,
        salt=salt_hex.encode("utf-8"),
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_SCRYPT_DKLEN,
        maxmem=_SCRYPT_MAXMEM,
    )
    return key.hex()


def hash_password(password: str) -> str:
    salt_hex = os.urandom(16).hex()
    return f"{salt_hex}:{_scrypt(password, salt_hex)}"


def verify_password(password: str, password_hash: str) -> bool:
    salt_hex, sep, stored_key_hex = password_hash.partition(":")
    if not sep:
        return False
    return hmac.compare_digest(_scrypt(password, salt_hex), stored_key_hex)


def generate_session_token() -> str:
    return uuid.uuid4().hex
