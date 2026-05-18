import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, JWT_SECRET_KEY

logger = logging.getLogger(__name__)

pwd_context = None  # lazy import below to keep jwt module focused


def _password_context():
    global pwd_context
    if pwd_context is None:
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
    return pwd_context


def hash_password(password: str) -> str:
    return _password_context().hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _password_context().verify(plain_password, hashed_password)


def normalize_bearer_token(token: str | None) -> str | None:
    """Strip whitespace and optional 'Bearer ' prefix (WebSocket query / REST header)."""
    if not token:
        return None
    value = token.strip()
    if value.lower().startswith("bearer "):
        value = value[7:].strip()
    return value or None


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    # Unix timestamp — same format REST and WebSocket decode expect
    to_encode["exp"] = int(expire.timestamp())

    encoded = jwt.encode(
        to_encode,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    # python-jose may return bytes on some versions — always return str for JSON/WS
    if isinstance(encoded, bytes):
        return encoded.decode("utf-8")
    return str(encoded)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and verify JWT using the same secret/algorithm as create_access_token.
    Raises jose.JWTError (or ExpiredSignatureError) on failure.
    """
    normalized = normalize_bearer_token(token)
    if not normalized:
        logger.warning("JWT decode failed: missing token")
        raise JWTError("Missing token")

    try:
        return jwt.decode(
            normalized,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"verify_aud": False},
        )
    except ExpiredSignatureError:
        logger.warning("JWT decode failed: token expired")
        raise
    except JWTError as exc:
        logger.warning(
            "JWT decode failed: %s (algorithm=%s, secret_len=%d)",
            exc,
            JWT_ALGORITHM,
            len(JWT_SECRET_KEY),
        )
        raise


def is_token_valid(token: str) -> bool:
    try:
        decode_access_token(token)
        return True
    except JWTError:
        return False
