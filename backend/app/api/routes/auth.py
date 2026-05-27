"""Authentication and API key management endpoints."""

import base64
import json
import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ApiKey, User, UserRole, Project
from app.api.deps import get_api_key, verify_project_access, get_validated_api_key, can_write_to_project, get_api_key_or_user
from app.config import get_settings
from app.services.google_auth import (
    get_authorization_url,
    exchange_code_for_tokens,
    get_user_info,
    verify_workspace_domain,
    extract_domain_from_email,
    GoogleAuthError,
)
from app.core.security import (
    create_access_token,
    get_current_user,
    get_current_active_user,
    TokenResponse,
)


router = APIRouter()


# Request/Response schemas
class ApiKeyCreate(BaseModel):
    """Request schema for creating a new API key."""
    name: str = Field(..., min_length=1, max_length=100)
    environment_ids: list[UUID] = Field(default_factory=list)
    project_id: Optional[UUID] = None


class ApiKeyResponse(BaseModel):
    """Response schema for API key (masked)."""
    id: UUID
    project_id: Optional[UUID] = None
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
    project_id: Optional[UUID] = None
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
    request: Request,
    key_data: ApiKeyCreate,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),  # Accept API key or JWT
    project: Optional[Project] = Depends(verify_project_access),
    validated_key: Optional[ApiKey] = Depends(get_validated_api_key),
):
    """
    Create a new API key.

    The full key is returned ONLY in this response - store it securely.
    Only the hash is stored in the database.
    """
    # Check write permissions (need at least member role to create API keys)
    if not can_write_to_project(db, _auth, project, validated_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create API keys in this project",
        )

    # Check for duplicate name within project scope
    query = db.query(ApiKey).filter(
        ApiKey.name == key_data.name,
        ApiKey.active == True,
    )
    if project:
        query = query.filter(ApiKey.project_id == project.id)
    existing = query.first()
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
        project_id=project.id if project else None,
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
        project_id=db_key.project_id,
        name=db_key.name,
        key=raw_key,
        key_prefix=key_prefix,
        environment_ids=db_key.environment_ids or [],
        created_at=db_key.created_at,
        active=db_key.active,
    )


@router.get("/auth/keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    request: Request,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
    project: Optional[Project] = Depends(verify_project_access),
):
    """
    List all API keys (masked), optionally filtered by project.

    Returns key metadata with masked keys (only prefix shown).
    """
    query = db.query(ApiKey).filter(ApiKey.active == True)
    if project:
        query = query.filter(ApiKey.project_id == project.id)
    keys = query.all()
    return [
        ApiKeyResponse(
            id=key.id,
            project_id=key.project_id,
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
    request: Request,
    key_id: UUID,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
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
        project_id=key.project_id,
        name=key.name,
        key_prefix=key.key_prefix,
        environment_ids=key.environment_ids or [],
        created_at=key.created_at,
        last_used_at=key.last_used_at,
        active=key.active,
    )


@router.delete("/auth/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    request: Request,
    key_id: UUID,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
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


# =============================================================================
# Google Workspace SSO Endpoints
# =============================================================================


class GoogleLoginResponse(BaseModel):
    """Response for Google login initiation."""
    authorization_url: str
    state: str


class UserResponse(BaseModel):
    """Response schema for authenticated user info."""
    id: UUID
    email: str
    name: str
    picture_url: Optional[str]
    workspace_domain: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class AuthCallbackResponse(BaseModel):
    """Response for successful authentication callback."""
    user: UserResponse
    token: TokenResponse


class CliTokenCreateResponse(BaseModel):
    """Response for CLI device-flow token creation."""
    nonce: str
    login_url: str
    expires_in: int


class CliTokenPollResponse(BaseModel):
    """Response for CLI device-flow token poll."""
    status: str
    access_token: Optional[str] = None
    expires_at: Optional[str] = None


@router.get("/auth/google/login")
async def google_login(request: Request, redirect: bool = True, cli_token: Optional[str] = None):
    """
    Initiate Google OAuth2 login flow.

    By default, redirects directly to Google for authentication.
    If redirect=false, returns the authorization URL as JSON for frontend use.
    If cli_token is provided, encodes the nonce into OAuth state for CLI device-flow.
    """
    settings = get_settings()

    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured",
        )

    if cli_token:
        # Encode nonce into composite state: "<random>.<b64url(nonce)>"
        encoded = base64.urlsafe_b64encode(cli_token.encode()).decode().rstrip("=")
        composite_state = f"{secrets.token_urlsafe(16)}.{encoded}"
        authorization_url, _ = get_authorization_url(state=composite_state)
        state = composite_state
    else:
        authorization_url, state = get_authorization_url()

    if redirect:
        return RedirectResponse(
            url=authorization_url,
            status_code=status.HTTP_302_FOUND,
        )

    return GoogleLoginResponse(
        authorization_url=authorization_url,
        state=state,
    )


@router.get("/auth/google/callback")
async def google_callback(
    code: str,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Handle Google OAuth2 callback.

    This endpoint is called by Google after the user authorizes the application.
    It exchanges the authorization code for tokens, verifies the workspace domain,
    creates or updates the user, and returns a JWT session token.

    For web applications, the token is set as an httpOnly cookie and the user
    is redirected to the frontend. For API usage, the token is returned in the
    response body.
    """
    settings = get_settings()

    # Handle OAuth errors from Google
    if error:
        error_msg = error_description or error
        # Redirect to frontend with error
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?error={error_msg}",
            status_code=status.HTTP_302_FOUND,
        )

    try:
        # Exchange code for tokens
        tokens = await exchange_code_for_tokens(code)

        # Get user info from Google
        google_user = await get_user_info(tokens.access_token)

        # Verify workspace domain
        allowed_domains = settings.allowed_workspace_domains_list
        print(f"DEBUG: User email={google_user.email}, allowed_domains={allowed_domains}")
        if allowed_domains and not verify_workspace_domain(google_user.email, allowed_domains):
            print(f"DEBUG: Domain rejected for {google_user.email}")
            return RedirectResponse(
                url=f"{settings.frontend_url}/login?error=domain_not_allowed",
                status_code=status.HTTP_302_FOUND,
            )

        # Find or create user
        user = db.query(User).filter(User.google_id == google_user.id).first()

        if user:
            # Update existing user
            user.email = google_user.email
            user.name = google_user.name
            user.picture_url = google_user.picture
            user.last_login = datetime.utcnow()
        else:
            # Create new user
            # First user becomes admin
            user_count = db.query(User).count()
            role = UserRole.admin if user_count == 0 else UserRole.user

            user = User(
                email=google_user.email,
                name=google_user.name,
                picture_url=google_user.picture,
                google_id=google_user.id,
                workspace_domain=extract_domain_from_email(google_user.email),
                role=role,
                is_active=True,
                last_login=datetime.utcnow(),
            )
            db.add(user)

        db.commit()
        db.refresh(user)

        # Create JWT token
        token_response = create_access_token(user.id, user.email)

        # ── CLI device-flow: write JWT to Redis nonce if present in state ──
        if state and "." in state:
            try:
                _, encoded = state.split(".", 1)
                padding = "=" * (4 - len(encoded) % 4)
                cli_token_nonce = base64.urlsafe_b64decode(encoded + padding).decode()
                import redis as _redis
                _settings = get_settings()
                _r = _redis.from_url(_settings.redis_url)
                try:
                    _key = f"sliples:cli_token:{cli_token_nonce}"
                    if _r.exists(_key):
                        expires_at = (
                            datetime.utcnow() + timedelta(hours=_settings.jwt_expiry_hours)
                        ).isoformat() + "Z"
                        _r.set(_key, json.dumps({
                            "status": "complete",
                            "access_token": token_response.access_token,
                            "expires_at": expires_at,
                        }), ex=300)
                        return RedirectResponse(
                            url=f"{settings.frontend_url}/auth/cli-success",
                            status_code=status.HTTP_302_FOUND,
                        )
                finally:
                    _r.close()
            except Exception:
                pass  # Not a CLI flow or malformed state — fall through to normal redirect
        # ── end CLI device-flow ──

        # Create redirect response with cookie
        response = RedirectResponse(
            url=f"{settings.frontend_url}/",
            status_code=status.HTTP_302_FOUND,
        )

        # Set httpOnly cookie with JWT
        response.set_cookie(
            key="access_token",
            value=token_response.access_token,
            httponly=True,
            secure=settings.frontend_url.startswith("https"),
            samesite="lax",
            max_age=settings.jwt_expiry_hours * 3600,
            path="/",
        )

        return response

    except GoogleAuthError as e:
        print(f"DEBUG: GoogleAuthError: {e.message}")
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?error={e.message}",
            status_code=status.HTTP_302_FOUND,
        )
    except Exception as e:
        import traceback
        print(f"DEBUG: Exception: {e}")
        traceback.print_exc()
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?error=authentication_failed",
            status_code=status.HTTP_302_FOUND,
        )


@router.post("/auth/logout")
async def logout(response: Response):
    """
    Log out the current user by clearing the session cookie.
    """
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        samesite="lax",
    )
    return {"message": "Successfully logged out"}


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get the currently authenticated user's information.

    Requires valid JWT authentication (cookie or Authorization header).
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture_url=current_user.picture_url,
        workspace_domain=current_user.workspace_domain,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
    )


@router.get("/auth/token", response_model=TokenResponse)
async def get_token(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a new JWT token for the current user.

    Useful for refreshing tokens before they expire.
    Requires valid JWT authentication.
    """
    return create_access_token(current_user.id, current_user.email)


# =============================================================================
# CLI Device-Flow Auth
# =============================================================================


@router.post("/auth/cli-token", response_model=CliTokenCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_cli_token():
    """
    Create a short-lived nonce for CLI device-flow auth.

    No authentication required. Returns a nonce and a login URL.
    The CLI opens the login URL in a browser, the user authenticates via Google,
    and the CLI polls GET /auth/cli-token/{nonce} until the JWT is ready.
    """
    import redis as _redis
    settings = get_settings()

    nonce = secrets.token_urlsafe(32)
    _r = _redis.from_url(settings.redis_url)
    try:
        _r.set(
            f"sliples:cli_token:{nonce}",
            json.dumps({"status": "pending"}),
            ex=120,
        )
    finally:
        _r.close()

    # Derive base API URL from google_redirect_uri (e.g. https://sliples.agantis.in/api/v1/auth/google/callback → https://sliples.agantis.in)
    from urllib.parse import urlparse
    _parsed = urlparse(settings.google_redirect_uri)
    api_base = f"{_parsed.scheme}://{_parsed.netloc}"
    login_url = f"{api_base}/api/v1/auth/google/login?cli_token={nonce}"
    return CliTokenCreateResponse(nonce=nonce, login_url=login_url, expires_in=120)


@router.get("/auth/cli-token/{nonce}", response_model=CliTokenPollResponse)
async def poll_cli_token(nonce: str):
    """
    Poll for a JWT after CLI device-flow login.

    Returns 202 while pending, 200 with JWT when complete, 404 if expired.
    """
    import redis as _redis
    from fastapi.responses import JSONResponse
    settings = get_settings()

    _r = _redis.from_url(settings.redis_url)
    try:
        raw = _r.get(f"sliples:cli_token:{nonce}")
    finally:
        _r.close()

    if raw is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CLI token not found or expired")

    data = json.loads(raw)

    if data["status"] == "complete":
        return CliTokenPollResponse(
            status="complete",
            access_token=data["access_token"],
            expires_at=data["expires_at"],
        )

    return JSONResponse(status_code=202, content={"status": "pending"})
