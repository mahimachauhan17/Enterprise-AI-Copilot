"""
Authentication Dependencies

FastAPI dependencies for extracting and validating the current user
from JWT tokens in request headers.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth.jwt_handler import verify_token
from backend.models.user import User
from backend.utils.logger import get_logger

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get the current authenticated user.

    Extracts the JWT token from the Authorization header,
    verifies it, and returns the corresponding User object.

    Args:
        token: JWT token from Authorization header.
        db: Database session.

    Returns:
        The authenticated User object.

    Raises:
        HTTPException: 401 if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        logger.warning(f"User not found for token sub: {user_id}")
        raise credentials_exception

    return user
