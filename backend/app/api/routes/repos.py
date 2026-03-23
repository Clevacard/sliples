"""Repository management endpoints."""

from uuid import UUID
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import ScenarioRepo, Project, ApiKey
from app.api.deps import (
    get_api_key_or_user,
    verify_project_access,
    get_validated_api_key,
    can_write_to_project,
)
from app.workers.tasks import sync_repository, sync_all_repositories

router = APIRouter()


class RepoCreate(BaseModel):
    name: str
    git_url: str
    branch: str = "main"
    sync_path: str = "scenarios"
    project_id: Optional[UUID] = None


class RepoResponse(BaseModel):
    id: UUID
    project_id: Optional[UUID] = None
    name: str
    git_url: str
    branch: str
    sync_path: str
    last_synced: Optional[datetime] = None

    class Config:
        from_attributes = True


@router.get("/repos", response_model=list[RepoResponse])
async def list_repos(
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
    project: Optional[Project] = Depends(verify_project_access),
):
    """List all configured scenario repositories, optionally filtered by project."""
    query = db.query(ScenarioRepo)
    if project:
        query = query.filter(ScenarioRepo.project_id == project.id)
    return query.all()


@router.post("/repos", response_model=RepoResponse, status_code=status.HTTP_201_CREATED)
async def create_repo(
    repo: RepoCreate,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
    project: Optional[Project] = Depends(verify_project_access),
    api_key: Optional[ApiKey] = Depends(get_validated_api_key),
):
    """Add a new scenario repository."""
    # Check write permissions
    if not can_write_to_project(db, auth, project, api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create repositories in this project",
        )

    # Check uniqueness within project scope
    query = db.query(ScenarioRepo).filter(ScenarioRepo.name == repo.name)
    if project:
        query = query.filter(ScenarioRepo.project_id == project.id)
    existing = query.first()
    if existing:
        raise HTTPException(status_code=400, detail="Repository with this name already exists")

    db_repo = ScenarioRepo(
        project_id=project.id if project else None,
        name=repo.name,
        git_url=repo.git_url,
        branch=repo.branch,
        sync_path=repo.sync_path,
    )
    db.add(db_repo)
    db.commit()
    db.refresh(db_repo)
    return db_repo


@router.post("/repos/{repo_id}/sync")
async def sync_repo(
    repo_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Sync scenarios from a specific repository."""
    repo = db.query(ScenarioRepo).filter(ScenarioRepo.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Queue the sync task
    task = sync_repository.delay(str(repo_id))

    return {
        "status": "sync_queued",
        "repo": repo.name,
        "task_id": task.id,
    }


@router.post("/repos/sync-all")
async def sync_all_repos(
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Sync scenarios from all repositories."""
    repos = db.query(ScenarioRepo).all()

    if not repos:
        return {"status": "no_repos", "repos": []}

    # Queue sync tasks for all repos
    task = sync_all_repositories.delay()

    return {
        "status": "sync_queued",
        "repos": [r.name for r in repos],
        "task_id": task.id,
    }


@router.delete("/repos/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repo(
    repo_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
    api_key: Optional[ApiKey] = Depends(get_validated_api_key),
):
    """Delete a repository and its scenarios."""
    repo = db.query(ScenarioRepo).filter(ScenarioRepo.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Check write permissions for the repo's project
    repo_project = db.query(Project).filter(Project.id == repo.project_id).first() if repo.project_id else None
    if not can_write_to_project(db, auth, repo_project, api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this repository",
        )

    db.delete(repo)
    db.commit()
