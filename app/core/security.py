"""Security utilities for authentication and authorization."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

# JWT settings
ALGORITHM = "HS256"
_BCRYPT_SHA256_PREFIX = "bcrypt_sha256$"


def _hash_password_bytes(password: str) -> bytes:
    """Return a fixed-length digest suitable for bcrypt."""

    return hashlib.sha256(password.encode("utf-8")).digest()


def _strip_prefix(hashed_password: str) -> str:
    """Return the raw bcrypt hash without our scheme prefix."""

    return hashed_password[len(_BCRYPT_SHA256_PREFIX) :]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    if not hashed_password:
        return False

    try:
        if not hashed_password.startswith(_BCRYPT_SHA256_PREFIX):
            return False

        hashed_bytes = _strip_prefix(hashed_password).encode("utf-8")
        return bcrypt.checkpw(_hash_password_bytes(plain_password), hashed_bytes)
    except ValueError:
        # bcrypt raises ValueError when input is invalid or when the stored hash is malformed.
        return False


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    hashed = bcrypt.hashpw(_hash_password_bytes(password), bcrypt.gensalt())
    return f"{_BCRYPT_SHA256_PREFIX}{hashed.decode('utf-8')}"


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    settings = get_settings()
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT access token."""
    try:
        settings = get_settings()
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
