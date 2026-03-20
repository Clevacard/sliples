"""Application configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://sliples:sliples_dev@localhost:5432/sliples"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # S3/MinIO
    s3_endpoint: str = "http://localhost:9000"
    s3_bucket: str = "sliples-screenshots"
    s3_access_key: str = "sliples"
    s3_secret_key: str = "sliples_dev"

    # Email
    smtp_host: str = "smtp.example.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "sliples@example.com"

    # Security
    secret_key: str = "change-this-in-production"
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # Google OAuth2 / Workspace SSO
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"
    allowed_workspace_domains: str = ""  # Comma-separated list, e.g., "example.com,corp.example.com"

    # JWT Settings
    jwt_secret_key: str = "jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # Frontend URL for OAuth redirects
    frontend_url: str = "http://localhost:5173"

    # Browsers
    browser_chrome_url: str = "ws://localhost:3001"
    browser_firefox_url: str = "ws://localhost:3002"

    # Retention
    retention_days: int = 365

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def allowed_workspace_domains_list(self) -> list[str]:
        """Parse allowed workspace domains from comma-separated string."""
        if not self.allowed_workspace_domains:
            return []
        return [domain.strip() for domain in self.allowed_workspace_domains.split(",") if domain.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
