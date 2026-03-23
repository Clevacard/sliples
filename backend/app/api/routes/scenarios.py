"""Scenario management endpoints."""

from uuid import UUID
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel

from app.database import get_db
from app.models import Scenario, ScenarioRepo, Project, ApiKey
from app.api.deps import (
    get_api_key_or_user,
    verify_project_access,
    get_validated_api_key,
    can_write_to_project,
)
from app.services.filesystem_sync import sync_filesystem_to_db

router = APIRouter()


class ScenarioResponse(BaseModel):
    id: UUID
    project_id: Optional[UUID] = None
    repo_id: Optional[UUID] = None
    name: str
    feature_path: str
    tags: list[str]
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScenarioDetail(ScenarioResponse):
    content: Optional[str]


class ScenariosByTagResponse(BaseModel):
    tag: str
    scenarios: list[ScenarioResponse]


class AllTagsResponse(BaseModel):
    tags: list[str]
    count: int


class ScenarioContentUpdate(BaseModel):
    content: str


class ScenarioCreate(BaseModel):
    name: str
    feature_path: str
    content: str
    tags: list[str] = []
    repo_id: Optional[UUID] = None


@router.get("/scenarios/tags", response_model=AllTagsResponse)
async def list_all_tags(
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
    project: Optional[Project] = Depends(verify_project_access),
):
    """Get a list of all unique tags across all scenarios."""
    query = db.query(Scenario.tags)
    if project:
        query = query.filter(Scenario.project_id == project.id)
    scenarios = query.all()

    all_tags = set()
    for (tags,) in scenarios:
        if tags:
            all_tags.update(tags)

    sorted_tags = sorted(all_tags)
    return AllTagsResponse(tags=sorted_tags, count=len(sorted_tags))


@router.get("/scenarios", response_model=list[ScenarioResponse])
async def list_scenarios(
    tag: Optional[str] = None,
    tags: Optional[str] = Query(None, description="Comma-separated list of tags (OR filter)"),
    repo_id: Optional[UUID] = None,
    search: Optional[str] = Query(None, description="Search in scenario name"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
    project: Optional[Project] = Depends(verify_project_access),
):
    """
    List all scenarios, optionally filtered by tag(s), repo, project, or search term.

    - Use `tag` for a single tag filter (scenarios containing this tag)
    - Use `tags` for multiple tags (comma-separated, OR logic)
    - Use `search` to filter by scenario name
    - Use `project_id` header or param to filter by project
    """
    query = db.query(Scenario)

    if project:
        query = query.filter(Scenario.project_id == project.id)

    if repo_id:
        query = query.filter(Scenario.repo_id == repo_id)

    if tag:
        query = query.filter(Scenario.tags.contains([tag]))
    elif tags:
        # Parse comma-separated tags and filter with OR logic
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            tag_filters = [Scenario.tags.contains([t]) for t in tag_list]
            query = query.filter(or_(*tag_filters))

    if search:
        query = query.filter(Scenario.name.ilike(f"%{search}%"))

    query = query.order_by(Scenario.name)
    return query.offset(offset).limit(limit).all()


@router.get("/scenarios/{scenario_id}", response_model=ScenarioDetail)
async def get_scenario(
    scenario_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Get a scenario by ID, including its full content."""
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.get("/scenarios/{scenario_id}/content")
async def get_scenario_content(
    scenario_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Get just the content of a scenario (Gherkin text)."""
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    return {
        "id": str(scenario.id),
        "name": scenario.name,
        "feature_path": scenario.feature_path,
        "content": scenario.content or "",
    }


@router.put("/scenarios/{scenario_id}/content", response_model=ScenarioDetail)
async def update_scenario_content(
    scenario_id: UUID,
    update: ScenarioContentUpdate,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Update the content (Gherkin text) of a scenario."""
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    scenario.content = update.content
    db.commit()
    db.refresh(scenario)
    return scenario


@router.post("/scenarios", response_model=ScenarioDetail, status_code=201)
async def create_scenario(
    scenario_data: ScenarioCreate,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
    project: Optional[Project] = Depends(verify_project_access),
    api_key: Optional[ApiKey] = Depends(get_validated_api_key),
):
    """Create a new scenario."""
    # Check write permissions
    if not can_write_to_project(db, auth, project, api_key):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to create scenarios in this project",
        )

    # Check if repo exists (if repo_id is provided)
    if scenario_data.repo_id:
        repo = db.query(ScenarioRepo).filter(ScenarioRepo.id == scenario_data.repo_id).first()
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")

    scenario = Scenario(
        project_id=project.id if project else None,
        name=scenario_data.name,
        feature_path=scenario_data.feature_path,
        content=scenario_data.content,
        tags=scenario_data.tags,
        repo_id=scenario_data.repo_id,
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.delete("/scenarios/{scenario_id}", status_code=204)
async def delete_scenario(
    scenario_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
    api_key: Optional[ApiKey] = Depends(get_validated_api_key),
):
    """Delete a scenario."""
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    # Check write permissions for the scenario's project
    scenario_project = db.query(Project).filter(Project.id == scenario.project_id).first() if scenario.project_id else None
    if not can_write_to_project(db, auth, scenario_project, api_key):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to delete this scenario",
        )

    db.delete(scenario)
    db.commit()
    return None


@router.post("/scenarios/sync")
async def sync_scenarios(
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """
    Sync scenarios from the local /scenarios filesystem folder.

    This scans all .feature files and:
    1. Adds new scenarios found on disk
    2. Updates scenarios whose content has changed
    3. Removes scenarios whose files have been deleted
    """
    stats = sync_filesystem_to_db(db)

    return {
        "status": "synced",
        "message": f"Scanned {stats['scanned']} files: {stats['added']} added, {stats['updated']} updated, {stats['deleted']} deleted",
        "stats": stats,
    }
