"""Settings API routes."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import get_settings, Settings

router = APIRouter(prefix="/settings", tags=["Settings"])


class EmailConfig(BaseModel):
    """Email configuration (read-only view)."""
    configured: bool
    host: str | None
    port: int | None
    from_address: str | None
    tls_enabled: bool


class StorageConfig(BaseModel):
    """Storage configuration (read-only view)."""
    configured: bool
    endpoint: str | None
    bucket: str | None
    access_key: str | None  # Masked
    region: str | None


class RetentionConfig(BaseModel):
    """Data retention configuration."""
    default_days: int
    cleanup_schedule: str
    last_cleanup: str | None


class SystemConfig(BaseModel):
    """System configuration response."""
    email: EmailConfig
    storage: StorageConfig
    retention: RetentionConfig


def mask_value(value: str | None, show_chars: int = 4) -> str | None:
    """Mask a sensitive value, showing only first/last few characters."""
    if not value:
        return None
    if len(value) <= show_chars * 2:
        return "*" * len(value)
    return value[:show_chars] + "*" * 8 + value[-show_chars:]


@router.get("/system", response_model=SystemConfig)
async def get_system_config(
    settings: Settings = Depends(get_settings),
) -> SystemConfig:
    """Get system configuration (read-only, for display in Settings UI)."""

    # Email config
    email_configured = bool(settings.smtp_host and settings.smtp_host != "smtp.example.com")
    email = EmailConfig(
        configured=email_configured,
        host=settings.smtp_host if email_configured else None,
        port=settings.smtp_port if email_configured else None,
        from_address=settings.email_from if email_configured else None,
        tls_enabled=settings.smtp_port == 587 or settings.smtp_port == 465,
    )

    # Storage config
    storage_configured = bool(settings.s3_endpoint and settings.s3_bucket)
    storage = StorageConfig(
        configured=storage_configured,
        endpoint=settings.s3_endpoint if storage_configured else None,
        bucket=settings.s3_bucket if storage_configured else None,
        access_key=mask_value(settings.s3_access_key) if storage_configured else None,
        region="us-east-1",  # Default, could be made configurable
    )

    # Retention config
    retention = RetentionConfig(
        default_days=settings.retention_days,
        cleanup_schedule="Daily at midnight",
        last_cleanup=None,  # Would be populated from a tracking table
    )

    return SystemConfig(
        email=email,
        storage=storage,
        retention=retention,
    )
