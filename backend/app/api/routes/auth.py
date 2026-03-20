"""Authentication and API key management endpoints."""

import secrets
from datetime import datetime
from typing import Optional
from uuid import UUID

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ApiKey
from app.api.deps import get_api_key


router = APIRouter()


# Request/Response schemas
class ApiKeyCreate(BaseModel):
    """Request schema for creating a new API key."""
    name: str = Field(..., min_length=1, max_length=100)
    environment_ids: list[UUID] = Field(default_factory=list)


class ApiKeyResponse(BaseModel):
    """Response schema for API key (masked)."""
    id: UUID
    name: str
    key_prefix: str
    environment_ids: list[UUID]
    created_at: datetime
    last_used_at: Optional[datetime]
    active: bool

    class Config:
        from_attributes = True


class ApiKeyCreatedResponse(BaseModel):
    """Response schema when a new API key is created (includes full key)."""
    id: UUID
    name: str
    key: str  # Full key - only returned on creation
    key_prefix: str
    environment_ids: list[UUID]
    created_at: datetime
    active: bool

    class Config:
        from_attributes = True


def generate_api_key() -> str:
    """Generate a secure random API key."""
    # Generate 32 random bytes and encode as hex (64 characters)
    return secrets.token_hex(32)


def hash_api_key(key: str) -> str:
    """Hash an API key using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(key.encode(), salt).decode()


@router.post("/auth/keys", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: ApiKeyCreate,
    db: Session = Depends(get_db),
    _api_key: str = Depends(get_api_key),  # Require authentication
):
    """
    Create a new API key.

    The full key is returned ONLY in this response - store it securely.
    Only the hash is stored in the database.
    """
    # Check for duplicate name
    existing = db.query(ApiKey).filter(
        ApiKey.name == key_data.name,
        ApiKey.active == True,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An active API key with this name already exists",
        )

    # Generate the key
    raw_key = generate_api_key()
    key_prefix = raw_key[:8]
    key_hash = hash_api_key(raw_key)

    # Create the API key record
    db_key = ApiKey(
        name=key_data.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        environment_ids=key_data.environment_ids,
        active=True,
    )
    db.add(db_key)
    db.commit()
    db.refresh(db_key)

    # Return response with the full key (only time it's returned)
    return ApiKeyCreatedResponse(
        id=db_key.id,
        name=db_key.name,
        key=raw_key,
        key_prefix=key_prefix,
        environment_ids=db_key.environment_ids or [],
        created_at=db_key.created_at,
        active=db_key.active,
    )


@router.get("/auth/keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    db: Session = Depends(get_db),
    _api_key: str = Depends(get_api_key),
):
    """
    List all API keys (masked).

    Returns key metadata with masked keys (only prefix shown).
    """
    keys = db.query(ApiKey).filter(ApiKey.active == True).all()
    return [
        ApiKeyResponse(
            id=key.id,
            name=key.name,
            key_prefix=key.key_prefix,
            environment_ids=key.environment_ids or [],
            created_at=key.created_at,
            last_used_at=key.last_used_at,
            active=key.active,
        )
        for key in keys
    ]


@router.get("/auth/keys/{key_id}", response_model=ApiKeyResponse)
async def get_api_key_by_id(
    key_id: UUID,
    db: Session = Depends(get_db),
    _api_key: str = Depends(get_api_key),
):
    """Get a specific API key by ID (masked)."""
    key = db.query(ApiKey).filter(
        ApiKey.id == key_id,
        ApiKey.active == True,
    ).first()

    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return ApiKeyResponse(
        id=key.id,
        name=key.name,
        key_prefix=key.key_prefix,
        environment_ids=key.environment_ids or [],
        created_at=key.created_at,
        last_used_at=key.last_used_at,
        active=key.active,
    )


@router.delete("/auth/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: UUID,
    db: Session = Depends(get_db),
    _api_key: str = Depends(get_api_key),
):
    """
    Revoke an API key.

    This performs a soft delete by setting active=False.
    """
    key = db.query(ApiKey).filter(
        ApiKey.id == key_id,
        ApiKey.active == True,
    ).first()

    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    # Soft delete - set active to False
    key.active = False
    db.commit()
