"""
JWT Token Handler

Creates and verifies JWT access tokens for user authentication.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data to encode (must include 'sub' key).
        expires_delta: Optional custom expiration time.

    Returns:
        Encoded JWT token string.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            hours=settings.JWT_EXPIRATION_HOURS
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

    logger.debug(f"Created access token for subject: {data.get('sub')}")
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token.

    Args:
        token: The JWT token string to verify.

    Returns:
        Decoded token payload.

    Raises:
        JWTError: If token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise
