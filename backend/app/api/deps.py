"""API dependencies."""

from typing import Optional, Union

from fastapi import Header, HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
import bcrypt

from app.database import get_db
from app.models import ApiKey, User


async def get_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> str:
    """
    Validate API key from header.

    For development, if no API keys exist in the database,
    any non-empty key is accepted (bootstrap mode).
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )

    # Check if any API keys exist (bootstrap mode)
    key_count = db.query(ApiKey).filter(ApiKey.active == True).count()

    if key_count == 0:
        # Bootstrap mode: accept any key for initial setup
        return x_api_key

    # Find key by prefix
    key_prefix = x_api_key[:8]
    api_key = db.query(ApiKey).filter(
        ApiKey.key_prefix == key_prefix,
        ApiKey.active == True,
    ).first()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Verify full key hash
    if not bcrypt.checkpw(x_api_key.encode(), api_key.key_hash.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Update last used timestamp
    from datetime import datetime
    api_key.last_used_at = datetime.utcnow()
    db.commit()

    return x_api_key


async def get_api_key_or_user(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> Union[str, User]:
    """
    Validate either API key or user JWT token.

    This allows endpoints to accept both API key authentication
    (for CI/CD integration) and user authentication (for web UI).

    Returns:
        Either the API key string or the User object
    """
    # Try API key first if provided
    if x_api_key:
        return await get_api_key(x_api_key=x_api_key, db=db)

    # Try JWT token from cookie or Authorization header
    from app.core.security import get_token_from_request, verify_access_token

    token = get_token_from_request(request)
    if token:
        token_data = verify_access_token(token)
        if token_data:
            user = db.query(User).filter(User.id == token_data.user_id).first()
            if user and user.is_active:
                return user

    # Neither auth method succeeded
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="API key or valid session required",
    )
