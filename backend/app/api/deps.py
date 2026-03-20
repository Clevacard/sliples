"""API dependencies."""

from typing import Optional

from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session
import bcrypt

from app.database import get_db
from app.models import ApiKey


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
