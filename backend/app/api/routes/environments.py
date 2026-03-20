"""Environment management endpoints."""

from uuid import UUID
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator, Field

from app.database import get_db
from app.models import Environment, BrowserConfig
from app.api.deps import get_api_key

router = APIRouter()

# Valid browser types
VALID_BROWSERS = {"chrome", "chromium", "firefox", "webkit", "edge"}
VALID_CHANNELS = {"stable", "beta", "dev", "canary"}


def validate_base_url(url: str) -> str:
    """Validate that base_url is a valid HTTP(S) URL."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL must use http or https scheme")
        if not parsed.netloc:
            raise ValueError("URL must have a valid host")
        # Normalize: remove trailing slash
        return url.rstrip("/")
    except Exception as e:
        raise ValueError(f"Invalid URL format: {e}")


class BrowserConfigCreate(BaseModel):
    browser: str = Field(..., description="Browser type: chrome, chromium, firefox, webkit, edge")
    version: str = "latest"
    channel: str = "stable"

    @field_validator("browser")
    @classmethod
    def validate_browser(cls, v: str) -> str:
        v = v.lower()
        if v not in VALID_BROWSERS:
            raise ValueError(f"Invalid browser. Must be one of: {', '.join(VALID_BROWSERS)}")
        return v

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v: str) -> str:
        v = v.lower()
        if v not in VALID_CHANNELS:
            raise ValueError(f"Invalid channel. Must be one of: {', '.join(VALID_CHANNELS)}")
        return v


class BrowserConfigResponse(BaseModel):
    id: UUID
    browser: str
    version: str
    channel: str

    class Config:
        from_attributes = True


class EnvironmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    base_url: str
    credentials_env: Optional[str] = None
    variables: dict = {}
    retention_days: int = Field(default=365, ge=1, le=3650)
    browser_configs: list[BrowserConfigCreate] = []

    @field_validator("base_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        return validate_base_url(v)


class EnvironmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    base_url: Optional[str] = None
    credentials_env: Optional[str] = None
    variables: Optional[dict] = None
    retention_days: Optional[int] = Field(None, ge=1, le=3650)
    browser_configs: Optional[list[BrowserConfigCreate]] = None

    @field_validator("base_url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_base_url(v)
        return v


class EnvironmentResponse(BaseModel):
    id: UUID
    name: str
    base_url: str
    credentials_env: Optional[str]
    variables: dict
    retention_days: int
    browser_configs: list[BrowserConfigResponse] = []

    class Config:
        from_attributes = True


@router.get("/environments", response_model=list[EnvironmentResponse])
async def list_environments(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """List all environments."""
    environments = db.query(Environment).all()
    return environments


@router.post("/environments", response_model=EnvironmentResponse, status_code=status.HTTP_201_CREATED)
async def create_environment(
    env: EnvironmentCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Create a new environment."""
    existing = db.query(Environment).filter(Environment.name == env.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Environment with this name already exists")

    db_env = Environment(
        name=env.name,
        base_url=env.base_url,
        credentials_env=env.credentials_env,
        variables=env.variables,
        retention_days=env.retention_days,
    )
    db.add(db_env)
    db.flush()  # Flush to get the environment ID

    # Add browser configs
    for bc in env.browser_configs:
        db_bc = BrowserConfig(
            environment_id=db_env.id,
            browser=bc.browser,
            version=bc.version,
            channel=bc.channel,
        )
        db.add(db_bc)

    db.commit()
    db.refresh(db_env)
    return db_env


@router.get("/environments/{environment_id}", response_model=EnvironmentResponse)
async def get_environment(
    environment_id: UUID,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Get an environment by ID."""
    env = db.query(Environment).filter(Environment.id == environment_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    return env


@router.put("/environments/{environment_id}", response_model=EnvironmentResponse)
async def update_environment(
    environment_id: UUID,
    env_update: EnvironmentUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Update an environment."""
    env = db.query(Environment).filter(Environment.id == environment_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    update_data = env_update.model_dump(exclude_unset=True)

    # Handle browser_configs separately
    browser_configs_data = update_data.pop("browser_configs", None)

    for field, value in update_data.items():
        setattr(env, field, value)

    # If browser_configs is provided, replace all existing configs
    if browser_configs_data is not None:
        # Delete existing configs
        db.query(BrowserConfig).filter(
            BrowserConfig.environment_id == environment_id
        ).delete()

        # Add new configs
        for bc_data in browser_configs_data:
            db_bc = BrowserConfig(
                environment_id=env.id,
                browser=bc_data["browser"],
                version=bc_data.get("version", "latest"),
                channel=bc_data.get("channel", "stable"),
            )
            db.add(db_bc)

    db.commit()
    db.refresh(env)
    return env


@router.delete("/environments/{environment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_environment(
    environment_id: UUID,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Delete an environment."""
    env = db.query(Environment).filter(Environment.id == environment_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    db.delete(env)
    db.commit()


# Browser Config Management Endpoints

@router.get(
    "/environments/{environment_id}/browsers",
    response_model=list[BrowserConfigResponse],
)
async def list_browser_configs(
    environment_id: UUID,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """List browser configurations for an environment."""
    env = db.query(Environment).filter(Environment.id == environment_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    return env.browser_configs


@router.post(
    "/environments/{environment_id}/browsers",
    response_model=BrowserConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_browser_config(
    environment_id: UUID,
    config: BrowserConfigCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Add a browser configuration to an environment."""
    env = db.query(Environment).filter(Environment.id == environment_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    # Check for duplicate browser/channel combo
    existing = db.query(BrowserConfig).filter(
        BrowserConfig.environment_id == environment_id,
        BrowserConfig.browser == config.browser,
        BrowserConfig.channel == config.channel,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Browser config for {config.browser}/{config.channel} already exists",
        )

    db_bc = BrowserConfig(
        environment_id=environment_id,
        browser=config.browser,
        version=config.version,
        channel=config.channel,
    )
    db.add(db_bc)
    db.commit()
    db.refresh(db_bc)
    return db_bc


@router.put(
    "/environments/{environment_id}/browsers/{browser_config_id}",
    response_model=BrowserConfigResponse,
)
async def update_browser_config(
    environment_id: UUID,
    browser_config_id: UUID,
    config: BrowserConfigCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Update a browser configuration."""
    env = db.query(Environment).filter(Environment.id == environment_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    db_bc = db.query(BrowserConfig).filter(
        BrowserConfig.id == browser_config_id,
        BrowserConfig.environment_id == environment_id,
    ).first()
    if not db_bc:
        raise HTTPException(status_code=404, detail="Browser config not found")

    db_bc.browser = config.browser
    db_bc.version = config.version
    db_bc.channel = config.channel

    db.commit()
    db.refresh(db_bc)
    return db_bc


@router.delete(
    "/environments/{environment_id}/browsers/{browser_config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_browser_config(
    environment_id: UUID,
    browser_config_id: UUID,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Delete a browser configuration."""
    env = db.query(Environment).filter(Environment.id == environment_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    db_bc = db.query(BrowserConfig).filter(
        BrowserConfig.id == browser_config_id,
        BrowserConfig.environment_id == environment_id,
    ).first()
    if not db_bc:
        raise HTTPException(status_code=404, detail="Browser config not found")

    db.delete(db_bc)
    db.commit()
