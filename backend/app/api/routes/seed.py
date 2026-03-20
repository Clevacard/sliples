"""Seed data management endpoints.

These endpoints allow administrators to populate or clear example data
in the database. Useful for demo environments and initial setup.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.api.deps import get_api_key
from app.seed_data import seed_database, clear_seed_data

router = APIRouter()


class SeedResponse(BaseModel):
    """Response model for seed operations."""
    environment: dict | None = None
    repository: dict | None = None
    custom_steps_count: int = 0
    schedules_count: int = 0
    scenarios_count: int = 0
    message: str


class ClearResponse(BaseModel):
    """Response model for clear operations."""
    deleted: dict
    message: str


@router.post(
    "/seed",
    response_model=SeedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Populate example data",
    description="""
    Populate the database with Giftstarr example data.

    This endpoint creates:
    - Environment: "Giftstarr Test" with base_url="https://test.giftstarr.cards"
    - Repository: "giftstarr-scenarios"
    - Custom step definitions for common Giftstarr actions
    - Example schedules (daily smoke test, weekly regression)
    - Sample scenario entries

    This operation is idempotent - running it multiple times will not create duplicates.
    Existing entities with the same names will be reused.

    **Authorization**: Requires a valid API key (admin access recommended).
    """,
)
async def create_seed_data(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
) -> SeedResponse:
    """
    Populate the database with example Giftstarr test data.

    This creates:
    - A test environment for https://test.giftstarr.cards
    - A repository configuration for Giftstarr scenarios
    - Custom step definitions for common testing actions
    - Example schedules for automated test runs
    """
    try:
        result = seed_database(db)
        return SeedResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed database: {str(e)}",
        )


@router.delete(
    "/seed",
    response_model=ClearResponse,
    status_code=status.HTTP_200_OK,
    summary="Clear example data",
    description="""
    Remove all Giftstarr example data from the database.

    This endpoint removes:
    - The "Giftstarr Test" environment (and its browser configurations)
    - The "giftstarr-scenarios" repository (and its scenarios/custom steps)
    - Related schedules

    **Warning**: This operation cannot be undone. Use with caution in production.

    **Authorization**: Requires a valid API key (admin access recommended).
    """,
)
async def delete_seed_data(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
) -> ClearResponse:
    """
    Clear all Giftstarr example data from the database.

    This removes the Giftstarr Test environment, giftstarr-scenarios
    repository, and all related entities (browser configs, scenarios,
    custom steps, and schedules).
    """
    try:
        result = clear_seed_data(db)
        return ClearResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear seed data: {str(e)}",
        )


@router.get(
    "/seed/status",
    summary="Check seed data status",
    description="Check if Giftstarr example data exists in the database.",
)
async def get_seed_status(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
) -> dict:
    """
    Check the current status of seed data in the database.

    Returns information about whether the Giftstarr example environment,
    repository, and related entities exist.
    """
    from app.models import Environment, ScenarioRepo, CustomStep, Schedule, Scenario
    from app.seed_data import GIFTSTARR_ENV_NAME, GIFTSTARR_REPO_NAME

    env = db.query(Environment).filter(Environment.name == GIFTSTARR_ENV_NAME).first()
    repo = db.query(ScenarioRepo).filter(ScenarioRepo.name == GIFTSTARR_REPO_NAME).first()

    result = {
        "seed_data_exists": env is not None and repo is not None,
        "environment": None,
        "repository": None,
        "custom_steps_count": 0,
        "schedules_count": 0,
        "scenarios_count": 0,
    }

    if env:
        result["environment"] = {
            "id": str(env.id),
            "name": env.name,
            "base_url": env.base_url,
        }
        result["schedules_count"] = db.query(Schedule).filter(
            Schedule.environment_id == env.id
        ).count()

    if repo:
        result["repository"] = {
            "id": str(repo.id),
            "name": repo.name,
            "git_url": repo.git_url,
        }
        result["custom_steps_count"] = db.query(CustomStep).filter(
            CustomStep.repo_id == repo.id
        ).count()
        result["scenarios_count"] = db.query(Scenario).filter(
            Scenario.repo_id == repo.id
        ).count()

    return result
