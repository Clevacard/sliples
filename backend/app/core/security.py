"""JWT utilities for user session management."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.user import User


class TokenData(BaseModel):
    """JWT token payload data."""
    user_id: str
    email: str
    exp: datetime


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


def create_access_token(user_id: UUID, email: str) -> TokenResponse:
    """
    Create a JWT access token for a user.

    Args:
        user_id: The user's UUID
        email: The user's email address

    Returns:
        TokenResponse with access token and metadata
    """
    settings = get_settings()

    expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiry_hours)
    expires_in_seconds = settings.jwt_expiry_hours * 3600

    to_encode = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )

    return TokenResponse(
        access_token=encoded_jwt,
        token_type="bearer",
        expires_in=expires_in_seconds,
    )


def verify_access_token(token: str) -> Optional[TokenData]:
    """
    Verify and decode a JWT access token.

    Args:
        token: The JWT token string

    Returns:
        TokenData if valid, None if invalid
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        user_id = payload.get("sub")
        email = payload.get("email")
        exp = payload.get("exp")

        if not user_id or not email:
            return None

        return TokenData(
            user_id=user_id,
            email=email,
            exp=datetime.fromtimestamp(exp) if exp else datetime.utcnow(),
        )
    except JWTError:
        return None


def get_token_from_request(request: Request) -> Optional[str]:
    """
    Extract JWT token from request (cookie or Authorization header).

    Checks:
    1. access_token cookie (preferred for web)
    2. Authorization: Bearer <token> header (for API clients)

    Args:
        request: FastAPI request object

    Returns:
        Token string if found, None otherwise
    """
    # Check cookie first (web browser)
    token = request.cookies.get("access_token")
    if token:
        return token

    # Check Authorization header (API clients)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]  # Remove "Bearer " prefix

    return None


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency to get the current authenticated user.

    Extracts JWT from cookie or Authorization header and validates it.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        User object if authenticated

    Raises:
        HTTPException 401 if not authenticated or invalid token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = get_token_from_request(request)
    if not token:
        raise credentials_exception

    token_data = verify_access_token(token)
    if not token_data:
        raise credentials_exception

    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    FastAPI dependency to get the current active user.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        User object if active

    Raises:
        HTTPException 403 if user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    FastAPI dependency to get the current admin user.

    Args:
        current_user: User from get_current_active_user dependency

    Returns:
        User object if admin

    Raises:
        HTTPException 403 if user is not an admin
    """
    from app.models.user import UserRole

    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
