"""Page management endpoints."""

from uuid import UUID
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import Page, PageEnvironmentOverride, Environment, Project, ApiKey
from app.api.deps import (
    get_api_key_or_user,
    verify_project_access,
    get_validated_api_key,
    can_write_to_project,
    get_required_project,
)

router = APIRouter()


class PageCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    path: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None


class PageUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    path: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None


class PageOverrideCreate(BaseModel):
    environment_id: UUID
    path: str = Field(..., min_length=1, max_length=500)


class PageOverrideResponse(BaseModel):
    id: UUID
    environment_id: UUID
    environment_name: Optional[str] = None
    path: str
    created_at: datetime

    class Config:
        from_attributes = True


class PageResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    path: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    overrides: list[PageOverrideResponse] = []

    class Config:
        from_attributes = True


class PageWithUrlsResponse(BaseModel):
    """Page with resolved URLs for all environments."""
    id: UUID
    project_id: UUID
    name: str
    path: str
    description: Optional[str]
    urls: dict[str, str]  # environment_name -> full_url


def page_to_response(page: Page) -> PageResponse:
    """Convert Page model to response."""
    return PageResponse(
        id=page.id,
        project_id=page.project_id,
        name=page.name,
        path=page.path,
        description=page.description,
        created_at=page.created_at,
        updated_at=page.updated_at,
        overrides=[
            PageOverrideResponse(
                id=o.id,
                environment_id=o.environment_id,
                environment_name=o.environment.name if o.environment else None,
                path=o.path,
                created_at=o.created_at,
            )
            for o in page.overrides
        ],
    )


@router.get("/pages", response_model=list[PageResponse])
async def list_pages(
    db: Session = Depends(get_db),
    auth=Depends(get_api_key_or_user),
    project: Project = Depends(get_required_project),
):
    """List all pages for the current project."""
    pages = db.query(Page).filter(Page.project_id == project.id).order_by(Page.name).all()
    return [page_to_response(p) for p in pages]


@router.post("/pages", response_model=PageResponse, status_code=status.HTTP_201_CREATED)
async def create_page(
    page_data: PageCreate,
    db: Session = Depends(get_db),
    auth=Depends(get_api_key_or_user),
    project: Project = Depends(get_required_project),
    api_key: Optional[ApiKey] = Depends(get_validated_api_key),
):
    """Create a new page."""
    if not can_write_to_project(db, auth, project, api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create pages in this project",
        )

    # Check for duplicate name
    existing = db.query(Page).filter(
        Page.project_id == project.id,
        Page.name == page_data.name,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A page named '{page_data.name}' already exists in this project",
        )

    page = Page(
        project_id=project.id,
        name=page_data.name,
        path=page_data.path,
        description=page_data.description,
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return page_to_response(page)


@router.get("/pages/{page_id}", response_model=PageResponse)
async def get_page(
    page_id: UUID,
    db: Session = Depends(get_db),
    auth=Depends(get_api_key_or_user),
):
    """Get a page by ID."""
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page_to_response(page)


@router.put("/pages/{page_id}", response_model=PageResponse)
async def update_page(
    page_id: UUID,
    page_data: PageUpdate,
    db: Session = Depends(get_db),
    auth=Depends(get_api_key_or_user),
    api_key: Optional[ApiKey] = Depends(get_validated_api_key),
):
    """Update a page."""
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Check permissions
    page_project = db.query(Project).filter(Project.id == page.project_id).first()
    if not can_write_to_project(db, auth, page_project, api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this page",
        )

    # Check for duplicate name if changing
    if page_data.name and page_data.name != page.name:
        existing = db.query(Page).filter(
            Page.project_id == page.project_id,
            Page.name == page_data.name,
            Page.id != page_id,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A page named '{page_data.name}' already exists in this project",
            )

    update_data = page_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(page, field, value)

    page.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(page)
    return page_to_response(page)


@router.delete("/pages/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page(
    page_id: UUID,
    db: Session = Depends(get_db),
    auth=Depends(get_api_key_or_user),
    api_key: Optional[ApiKey] = Depends(get_validated_api_key),
):
    """Delete a page."""
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Check permissions
    page_project = db.query(Project).filter(Project.id == page.project_id).first()
    if not can_write_to_project(db, auth, page_project, api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this page",
        )

    db.delete(page)
    db.commit()


# =============================================================================
# Environment Overrides
# =============================================================================


@router.post("/pages/{page_id}/overrides", response_model=PageOverrideResponse, status_code=status.HTTP_201_CREATED)
async def create_page_override(
    page_id: UUID,
    override_data: PageOverrideCreate,
    db: Session = Depends(get_db),
    auth=Depends(get_api_key_or_user),
    api_key: Optional[ApiKey] = Depends(get_validated_api_key),
):
    """Create a path override for a specific environment."""
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Check permissions
    page_project = db.query(Project).filter(Project.id == page.project_id).first()
    if not can_write_to_project(db, auth, page_project, api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this page",
        )

    # Verify environment exists and belongs to the same project
    env = db.query(Environment).filter(Environment.id == override_data.environment_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    if env.project_id != page.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Environment must belong to the same project as the page",
        )

    # Check for existing override
    existing = db.query(PageEnvironmentOverride).filter(
        PageEnvironmentOverride.page_id == page_id,
        PageEnvironmentOverride.environment_id == override_data.environment_id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An override for this environment already exists",
        )

    override = PageEnvironmentOverride(
        page_id=page_id,
        environment_id=override_data.environment_id,
        path=override_data.path,
    )
    db.add(override)
    db.commit()
    db.refresh(override)

    return PageOverrideResponse(
        id=override.id,
        environment_id=override.environment_id,
        environment_name=env.name,
        path=override.path,
        created_at=override.created_at,
    )


@router.delete("/pages/{page_id}/overrides/{override_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page_override(
    page_id: UUID,
    override_id: UUID,
    db: Session = Depends(get_db),
    auth=Depends(get_api_key_or_user),
    api_key: Optional[ApiKey] = Depends(get_validated_api_key),
):
    """Delete a path override."""
    override = db.query(PageEnvironmentOverride).filter(
        PageEnvironmentOverride.id == override_id,
        PageEnvironmentOverride.page_id == page_id,
    ).first()
    if not override:
        raise HTTPException(status_code=404, detail="Override not found")

    # Check permissions
    page = db.query(Page).filter(Page.id == page_id).first()
    page_project = db.query(Project).filter(Project.id == page.project_id).first()
    if not can_write_to_project(db, auth, page_project, api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this page",
        )

    db.delete(override)
    db.commit()


# =============================================================================
# URL Resolution
# =============================================================================


@router.get("/pages/{page_id}/urls", response_model=PageWithUrlsResponse)
async def get_page_urls(
    page_id: UUID,
    db: Session = Depends(get_db),
    auth=Depends(get_api_key_or_user),
):
    """Get a page with resolved URLs for all project environments."""
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Get all environments for the project
    environments = db.query(Environment).filter(
        Environment.project_id == page.project_id
    ).all()

    # Build override lookup
    override_map = {o.environment_id: o.path for o in page.overrides}

    # Resolve URLs
    urls = {}
    for env in environments:
        path = override_map.get(env.id, page.path)
        # Ensure proper URL joining
        base = env.base_url.rstrip("/")
        path = path if path.startswith("/") else f"/{path}"
        urls[env.name] = f"{base}{path}"

    return PageWithUrlsResponse(
        id=page.id,
        project_id=page.project_id,
        name=page.name,
        path=page.path,
        description=page.description,
        urls=urls,
    )


@router.get("/pages/resolve/{page_name}")
async def resolve_page_url(
    page_name: str,
    environment_id: UUID,
    db: Session = Depends(get_db),
    auth=Depends(get_api_key_or_user),
    project: Project = Depends(get_required_project),
):
    """Resolve a page name to a full URL for a specific environment.

    This is the endpoint used by the test runner to resolve page names
    in Gherkin steps like: When I navigate to the "Login" page
    """
    # Find the page
    page = db.query(Page).filter(
        Page.project_id == project.id,
        Page.name == page_name,
    ).first()
    if not page:
        raise HTTPException(
            status_code=404,
            detail=f"Page '{page_name}' not found in project",
        )

    # Find the environment
    env = db.query(Environment).filter(Environment.id == environment_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    # Check for override
    override = db.query(PageEnvironmentOverride).filter(
        PageEnvironmentOverride.page_id == page.id,
        PageEnvironmentOverride.environment_id == environment_id,
    ).first()

    path = override.path if override else page.path

    # Build full URL
    base = env.base_url.rstrip("/")
    path = path if path.startswith("/") else f"/{path}"
    full_url = f"{base}{path}"

    return {
        "page_name": page_name,
        "environment_name": env.name,
        "path": path,
        "base_url": env.base_url,
        "full_url": full_url,
    }
