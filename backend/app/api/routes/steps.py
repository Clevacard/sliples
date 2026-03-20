"""Custom step definition endpoints."""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import CustomStep, ScenarioRepo
from app.api.deps import get_api_key_or_user

router = APIRouter()


class StepCreate(BaseModel):
    repo_id: Optional[UUID] = None
    name: str
    pattern: str
    code: str


class StepUpdate(BaseModel):
    name: Optional[str] = None
    pattern: Optional[str] = None
    code: Optional[str] = None


class StepResponse(BaseModel):
    id: UUID
    repo_id: Optional[UUID]
    name: str
    pattern: str
    code: str
    committed: bool

    class Config:
        from_attributes = True


@router.get("/steps/custom", response_model=list[StepResponse])
async def list_custom_steps(
    repo_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """List all custom step definitions."""
    query = db.query(CustomStep)
    if repo_id:
        query = query.filter(CustomStep.repo_id == repo_id)
    return query.all()


@router.post("/steps/custom", response_model=StepResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_step(
    step: StepCreate,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Create a new custom step definition."""
    # Validate repo if provided
    if step.repo_id:
        repo = db.query(ScenarioRepo).filter(ScenarioRepo.id == step.repo_id).first()
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")

    # Check for duplicate pattern
    existing = db.query(CustomStep).filter(CustomStep.pattern == step.pattern).first()
    if existing:
        raise HTTPException(status_code=400, detail="Step with this pattern already exists")

    db_step = CustomStep(
        repo_id=step.repo_id,
        name=step.name,
        pattern=step.pattern,
        code=step.code,
    )
    db.add(db_step)
    db.commit()
    db.refresh(db_step)
    return db_step


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

    update_data = step_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(step, field, value)

    # Mark as uncommitted if code changed
    if "code" in update_data or "pattern" in update_data:
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


@router.delete("/steps/custom/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_step(
    step_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Delete a custom step definition."""
    step = db.query(CustomStep).filter(CustomStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")

    db.delete(step)
    db.commit()
