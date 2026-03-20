"""Browser configuration endpoints."""

from fastapi import APIRouter, Depends

from app.api.deps import get_api_key_or_user

router = APIRouter()


@router.get("/browsers")
async def list_browsers(
    auth = Depends(get_api_key_or_user),
):
    """List available browsers and their versions."""
    return {
        "browsers": [
            {
                "name": "chrome",
                "display_name": "Google Chrome",
                "versions": ["latest", "stable", "beta", "dev"],
                "default": "latest",
            },
            {
                "name": "firefox",
                "display_name": "Mozilla Firefox",
                "versions": ["latest", "stable", "beta", "dev"],
                "default": "latest",
            },
        ],
        "note": "Version pinning to specific versions available in Phase 3",
    }
