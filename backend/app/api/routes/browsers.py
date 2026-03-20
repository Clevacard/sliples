"""Browser configuration endpoints."""

from fastapi import APIRouter, Depends

from app.api.deps import get_api_key

router = APIRouter()


@router.get("/browsers")
async def list_browsers(
    api_key: str = Depends(get_api_key),
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
