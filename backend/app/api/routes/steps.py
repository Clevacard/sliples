"""Custom step definition endpoints."""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import CustomStep, ScenarioRepo, Project, ApiKey
from app.api.deps import (
    get_api_key_or_user,
    verify_project_access,
    get_validated_api_key,
    can_write_to_project,
)

router = APIRouter()


class StepCreate(BaseModel):
    repo_id: Optional[UUID] = None
    name: str
    pattern: str
    code: Optional[str] = None
    implementation: Optional[str] = None  # Alias for code (frontend compatibility)
    description: Optional[str] = None

    def get_code(self) -> str:
        """Get code from either field."""
        return self.code or self.implementation or ""


class StepUpdate(BaseModel):
    name: Optional[str] = None
    pattern: Optional[str] = None
    code: Optional[str] = None
    implementation: Optional[str] = None  # Alias for code (frontend compatibility)
    description: Optional[str] = None

    def get_code(self) -> Optional[str]:
        """Get code from either field."""
        return self.code or self.implementation


class StepResponse(BaseModel):
    id: UUID
    project_id: Optional[UUID] = None
    repo_id: Optional[UUID]
    name: str
    pattern: str
    code: str
    committed: bool

    class Config:
        from_attributes = True


@router.get("/steps", response_model=list[StepResponse])
@router.get("/steps/custom", response_model=list[StepResponse])
async def list_custom_steps(
    repo_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
    project: Optional[Project] = Depends(verify_project_access),
):
    """List all custom step definitions, optionally filtered by project."""
    query = db.query(CustomStep)
    if project:
        query = query.filter(CustomStep.project_id == project.id)
    if repo_id:
        query = query.filter(CustomStep.repo_id == repo_id)
    return query.all()


@router.post("/steps", response_model=StepResponse, status_code=status.HTTP_201_CREATED)
@router.post("/steps/custom", response_model=StepResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_step(
    step: StepCreate,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
    project: Optional[Project] = Depends(verify_project_access),
    api_key: Optional[ApiKey] = Depends(get_validated_api_key),
):
    """Create a new custom step definition."""
    # Check write permissions
    if not can_write_to_project(db, auth, project, api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create steps in this project",
        )

    # Validate repo if provided
    if step.repo_id:
        repo = db.query(ScenarioRepo).filter(ScenarioRepo.id == step.repo_id).first()
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")

    # Check for duplicate pattern within project scope
    query = db.query(CustomStep).filter(CustomStep.pattern == step.pattern)
    if project:
        query = query.filter(CustomStep.project_id == project.id)
    existing = query.first()
    if existing:
        raise HTTPException(status_code=400, detail="Step with this pattern already exists")

    db_step = CustomStep(
        project_id=project.id if project else None,
        repo_id=step.repo_id,
        name=step.name,
        pattern=step.pattern,
        code=step.get_code(),
    )
    db.add(db_step)
    db.commit()
    db.refresh(db_step)
    return db_step


@router.put("/steps/{step_id}", response_model=StepResponse)
@router.put("/steps/custom/{step_id}", response_model=StepResponse)
async def update_custom_step(
    step_id: UUID,
    step_update: StepUpdate,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Update a custom step definition."""
    step = db.query(CustomStep).filter(CustomStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")

    # Handle field updates
    if step_update.name is not None:
        step.name = step_update.name
    if step_update.pattern is not None:
        step.pattern = step_update.pattern

    # Handle code/implementation (frontend sends 'implementation')
    new_code = step_update.get_code()
    if new_code is not None:
        step.code = new_code

    # Mark as uncommitted if code or pattern changed
    if step_update.pattern is not None or new_code is not None:
        step.committed = False

    db.commit()
    db.refresh(step)
    return step


@router.post("/steps/custom/{step_id}/save-to-repo")
async def save_step_to_repo(
    step_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Commit a custom step definition to its repository."""
    step = db.query(CustomStep).filter(CustomStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")

    if not step.repo_id:
        raise HTTPException(status_code=400, detail="Step is not associated with a repository")

    # TODO: Implement git commit
    step.committed = True
    db.commit()

    return {"status": "committed", "step_id": str(step_id)}


@router.delete("/steps/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/steps/custom/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_step(
    step_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
    api_key: Optional[ApiKey] = Depends(get_validated_api_key),
):
    """Delete a custom step definition."""
    step = db.query(CustomStep).filter(CustomStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")

    # Check write permissions for the step's project
    step_project = db.query(Project).filter(Project.id == step.project_id).first() if step.project_id else None
    if not can_write_to_project(db, auth, step_project, api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this step",
        )

    db.delete(step)
    db.commit()
