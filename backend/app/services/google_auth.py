"""Google OAuth2 service for Workspace SSO authentication."""

import secrets
from typing import Optional
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel

from app.config import get_settings


class GoogleUserInfo(BaseModel):
    """User information from Google."""
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    hd: Optional[str] = None  # Hosted domain (Google Workspace domain)


class GoogleTokens(BaseModel):
    """OAuth tokens from Google."""
    access_token: str
    id_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: int
    token_type: str


class GoogleAuthError(Exception):
    """Exception for Google authentication errors."""

    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


# Google OAuth2 endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def get_authorization_url(state: Optional[str] = None) -> tuple[str, str]:
    """
    Generate the Google OAuth2 authorization URL.

    Args:
        state: Optional state parameter for CSRF protection.
               If not provided, a random state will be generated.

    Returns:
        Tuple of (authorization_url, state)
    """
    settings = get_settings()

    if state is None:
        state = secrets.token_urlsafe(32)

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "state": state,
        "prompt": "select_account",  # Always show account selector
    }

    # Note: We don't set the 'hd' parameter here to allow users to select
    # any Google account. Domain validation happens server-side after auth.

    authorization_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return authorization_url, state


async def exchange_code_for_tokens(code: str) -> GoogleTokens:
    """
    Exchange authorization code for access and ID tokens.

    Args:
        code: The authorization code from Google callback

    Returns:
        GoogleTokens containing access_token and optional refresh_token

    Raises:
        GoogleAuthError if token exchange fails
    """
    settings = get_settings()

    data = {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.google_redirect_uri,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            error_data = response.json()
            raise GoogleAuthError(
                message=error_data.get("error_description", "Token exchange failed"),
                error_code=error_data.get("error"),
            )

        token_data = response.json()
        return GoogleTokens(
            access_token=token_data["access_token"],
            id_token=token_data.get("id_token"),
            refresh_token=token_data.get("refresh_token"),
            expires_in=token_data["expires_in"],
            token_type=token_data["token_type"],
        )


async def get_user_info(access_token: str) -> GoogleUserInfo:
    """
    Fetch user profile information from Google.

    Args:
        access_token: Valid Google access token

    Returns:
        GoogleUserInfo with user profile data

    Raises:
        GoogleAuthError if fetching user info fails
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if response.status_code != 200:
            raise GoogleAuthError(
                message="Failed to fetch user info",
                error_code="userinfo_error",
            )

        user_data = response.json()
        return GoogleUserInfo(
            id=user_data["id"],
            email=user_data["email"],
            name=user_data.get("name", user_data["email"]),
            picture=user_data.get("picture"),
            hd=user_data.get("hd"),  # Hosted domain for Workspace users
        )


def verify_workspace_domain(email: str, allowed_domains: list[str]) -> bool:
    """
    Verify that the user's email domain is in the allowed workspace domains.

    Args:
        email: User's email address
        allowed_domains: List of allowed domain names (e.g., ["example.com", "corp.example.com"])

    Returns:
        True if domain is allowed, False otherwise
    """
    if not allowed_domains:
        # If no domains configured, allow all (not recommended for production)
        return True

    # Extract domain from email
    if "@" not in email:
        return False

    email_domain = email.split("@")[1].lower()

    # Check if domain matches any allowed domain
    return email_domain in [d.lower() for d in allowed_domains]


def extract_domain_from_email(email: str) -> str:
    """
    Extract the domain part from an email address.

    Args:
        email: Email address

    Returns:
        Domain part of the email
    """
    if "@" not in email:
        return ""
    return email.split("@")[1].lower()
