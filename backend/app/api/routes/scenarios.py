"""Scenario management endpoints."""

from uuid import UUID
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel

from app.database import get_db
from app.models import Scenario, ScenarioRepo
from app.api.deps import get_api_key_or_user
from app.workers.tasks import sync_all_repositories

router = APIRouter()


class ScenarioResponse(BaseModel):
    id: UUID
    repo_id: Optional[UUID]
    name: str
    feature_path: str
    tags: list[str]
    updated_at: Optional[datetime]

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


@router.get("/scenarios/tags", response_model=AllTagsResponse)
async def list_all_tags(
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Get a list of all unique tags across all scenarios."""
    scenarios = db.query(Scenario.tags).all()

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
):
    """
    List all scenarios, optionally filtered by tag(s), repo, or search term.

    - Use `tag` for a single tag filter (scenarios containing this tag)
    - Use `tags` for multiple tags (comma-separated, OR logic)
    - Use `search` to filter by scenario name
    """
    query = db.query(Scenario)

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


@router.post("/scenarios/sync")
async def sync_scenarios(
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """
    Sync scenarios from all configured repositories.

    This triggers background tasks to:
    1. Clone/pull each repository
    2. Parse all .feature files
    3. Update the database with extracted scenarios
    """
    repos = db.query(ScenarioRepo).all()

    if not repos:
        return {
            "status": "no_repos",
            "message": "No repositories configured. Add a repository first.",
            "synced_count": 0,
        }

    # Queue the sync task
    task = sync_all_repositories.delay()

    return {
        "status": "sync_queued",
        "message": f"Sync started for {len(repos)} repositories",
        "task_id": task.id,
        "repos": [{"id": str(r.id), "name": r.name} for r in repos],
    }
