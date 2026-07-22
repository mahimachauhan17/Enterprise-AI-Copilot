"""
Authentication API Routes

Handles user signup and login with JWT token generation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import bcrypt

from backend.database import get_db
from backend.models.user import User
from backend.schemas.user import UserCreate, UserLogin, TokenResponse, UserResponse
from backend.auth.jwt_handler import create_access_token
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["Authentication"])


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.

    Creates a new user with hashed password and returns a JWT token.

    Args:
        user_data: Username, email, and password.
        db: Database session.

    Returns:
        JWT access token and user data.

    Raises:
        HTTPException 400: If email or username already exists.
    """
    # Check for existing email
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check for existing username
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # Create user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate token
    access_token = create_access_token(data={"sub": str(new_user.id)})

    logger.info(f"New user registered: {new_user.username} ({new_user.email})")

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(new_user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate a user and return a JWT token.

    Args:
        user_data: Email and password.
        db: Database session.

    Returns:
        JWT access token and user data.

    Raises:
        HTTPException 401: If credentials are invalid.
    """
    # Find user by email
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(user_data.password, str(user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Generate token
    access_token = create_access_token(data={"sub": str(user.id)})

    logger.info(f"User logged in: {user.username}")

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )
