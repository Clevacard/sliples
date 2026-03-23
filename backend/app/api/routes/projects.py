"""Project management endpoints."""

import re
from uuid import UUID
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator

from app.database import get_db
from app.models import Project, ProjectMember, ProjectRole, User, UserRole, ApiKey
from app.api.deps import get_current_user, get_api_key_or_user, get_validated_api_key

router = APIRouter()


# Request/Response schemas
class ProjectCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$", v):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens, and cannot start/end with hyphen")
        if len(v) < 2 or len(v) > 100:
            raise ValueError("Slug must be between 2 and 100 characters")
        return v


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectMemberCreate(BaseModel):
    email: str
    role: ProjectRole = ProjectRole.member


class ProjectMemberUpdate(BaseModel):
    role: ProjectRole


class ProjectMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    email: str
    name: str
    role: ProjectRole
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    member_count: Optional[int] = None
    current_user_role: Optional[ProjectRole] = None

    class Config:
        from_attributes = True


class ProjectDetailResponse(ProjectResponse):
    members: list[ProjectMemberResponse] = []


def generate_slug(name: str) -> str:
    """Generate a URL-safe slug from a name."""
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:100] if slug else "project"


def get_project_with_access(
    project_id: UUID,
    db: Session,
    user: User,
    minimum_role: Optional[ProjectRole] = None,
) -> tuple[Project, ProjectMember]:
    """Get a project and verify user has access."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Global admins have full access
    if user.role == UserRole.admin:
        # Return a synthetic membership for admins
        return project, ProjectMember(role=ProjectRole.owner)

    # Check membership
    membership = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user.id,
    ).first()

    if not membership:
        raise HTTPException(status_code=403, detail="You don't have access to this project")

    # Check minimum role if specified
    if minimum_role:
        role_hierarchy = {
            ProjectRole.viewer: 0,
            ProjectRole.member: 1,
            ProjectRole.admin: 2,
            ProjectRole.owner: 3,
        }
        if role_hierarchy[membership.role] < role_hierarchy[minimum_role]:
            raise HTTPException(
                status_code=403,
                detail=f"This action requires at least {minimum_role.value} role",
            )

    return project, membership


@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
    api_key: Optional[ApiKey] = Depends(get_validated_api_key),
):
    """List all projects the current user/API key has access to."""
    # API key auth - return projects the key has access to
    if isinstance(auth, str):
        if api_key and api_key.project_id:
            # Scoped API key - return only that project
            project = db.query(Project).filter(Project.id == api_key.project_id).first()
            return [project] if project else []
        # Global API key - return all projects
        projects = db.query(Project).order_by(Project.name).all()
        return [
            ProjectResponse(
                id=p.id,
                name=p.name,
                slug=p.slug,
                description=p.description,
                created_at=p.created_at,
                updated_at=p.updated_at,
                member_count=db.query(ProjectMember).filter(ProjectMember.project_id == p.id).count(),
                current_user_role=None,
            )
            for p in projects
        ]

    # User auth
    user: User = auth

    # Global admins see all projects
    if user.role == UserRole.admin:
        projects = db.query(Project).order_by(Project.name).all()
        result = []
        for p in projects:
            result.append(ProjectResponse(
                id=p.id,
                name=p.name,
                slug=p.slug,
                description=p.description,
                created_at=p.created_at,
                updated_at=p.updated_at,
                member_count=len(p.members),
                current_user_role=ProjectRole.owner,
            ))
        return result

    # Regular users see only their projects
    memberships = db.query(ProjectMember).filter(
        ProjectMember.user_id == user.id
    ).all()

    result = []
    for m in memberships:
        p = m.project
        result.append(ProjectResponse(
            id=p.id,
            name=p.name,
            slug=p.slug,
            description=p.description,
            created_at=p.created_at,
            updated_at=p.updated_at,
            member_count=len(p.members),
            current_user_role=m.role,
        ))

    return sorted(result, key=lambda x: x.name)


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Create a new project. The creator becomes the owner. Requires user authentication (not API key)."""
    # API key auth cannot create projects (no user to be owner)
    if isinstance(auth, str):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Creating projects requires user authentication. Please log in via Google OAuth.",
        )

    user: User = auth
    # Generate slug if not provided
    slug = data.slug or generate_slug(data.name)

    # Check for slug uniqueness
    existing = db.query(Project).filter(Project.slug == slug).first()
    if existing:
        # Try appending a number
        base_slug = slug
        counter = 1
        while existing:
            slug = f"{base_slug}-{counter}"
            existing = db.query(Project).filter(Project.slug == slug).first()
            counter += 1

    project = Project(
        name=data.name,
        slug=slug,
        description=data.description,
    )
    db.add(project)
    db.flush()

    # Add creator as owner
    membership = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role=ProjectRole.owner,
    )
    db.add(membership)
    db.commit()
    db.refresh(project)

    return ProjectResponse(
        id=project.id,
        name=project.name,
        slug=project.slug,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        member_count=1,
        current_user_role=ProjectRole.owner,
    )


@router.get("/projects/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
    api_key: Optional[ApiKey] = Depends(get_validated_api_key),
):
    """Get project details including members."""
    # API key auth - check if key has access to this project
    if isinstance(auth, str):
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if api_key and api_key.project_id and api_key.project_id != project_id:
            raise HTTPException(status_code=403, detail="API key does not have access to this project")

        members = []
        for m in project.members:
            members.append(ProjectMemberResponse(
                id=m.id,
                user_id=m.user_id,
                email=m.user.email,
                name=m.user.name,
                role=m.role,
                created_at=m.created_at,
            ))
        return ProjectDetailResponse(
            id=project.id,
            name=project.name,
            slug=project.slug,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at,
            member_count=len(members),
            current_user_role=None,
            members=members,
        )

    user: User = auth
    project, membership = get_project_with_access(project_id, db, user)

    members = []
    for m in project.members:
        members.append(ProjectMemberResponse(
            id=m.id,
            user_id=m.user_id,
            email=m.user.email,
            name=m.user.name,
            role=m.role,
            created_at=m.created_at,
        ))

    return ProjectDetailResponse(
        id=project.id,
        name=project.name,
        slug=project.slug,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        member_count=len(members),
        current_user_role=membership.role,
        members=members,
    )


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Update project details. Requires admin or owner role (user auth only)."""
    if isinstance(auth, str):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Updating projects requires user authentication. Please log in.",
        )

    user: User = auth
    project, membership = get_project_with_access(project_id, db, user, minimum_role=ProjectRole.admin)

    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description

    db.commit()
    db.refresh(project)

    return ProjectResponse(
        id=project.id,
        name=project.name,
        slug=project.slug,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        member_count=len(project.members),
        current_user_role=membership.role,
    )


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Delete a project. Requires owner role (user auth only)."""
    if isinstance(auth, str):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Deleting projects requires user authentication. Please log in.",
        )

    user: User = auth
    project, _ = get_project_with_access(project_id, db, user, minimum_role=ProjectRole.owner)

    db.delete(project)
    db.commit()


# Member management endpoints

@router.get("/projects/{project_id}/members", response_model=list[ProjectMemberResponse])
async def list_project_members(
    project_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
    api_key: Optional[ApiKey] = Depends(get_validated_api_key),
):
    """List all members of a project."""
    # API key auth - check access
    if isinstance(auth, str):
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if api_key and api_key.project_id and api_key.project_id != project_id:
            raise HTTPException(status_code=403, detail="API key does not have access to this project")
    else:
        user: User = auth
        project, _ = get_project_with_access(project_id, db, user)

    members = []
    for m in project.members:
        members.append(ProjectMemberResponse(
            id=m.id,
            user_id=m.user_id,
            email=m.user.email,
            name=m.user.name,
            role=m.role,
            created_at=m.created_at,
        ))

    return members


@router.post("/projects/{project_id}/members", response_model=ProjectMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_project_member(
    project_id: UUID,
    data: ProjectMemberCreate,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Add a member to the project. Requires admin or owner role (user auth only)."""
    if isinstance(auth, str):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Managing project members requires user authentication. Please log in.",
        )

    user: User = auth
    project, _ = get_project_with_access(project_id, db, user, minimum_role=ProjectRole.admin)

    # Find user by email
    new_member_user = db.query(User).filter(User.email == data.email).first()
    if not new_member_user:
        raise HTTPException(status_code=404, detail="User not found with this email")

    # Check if already a member
    existing = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == new_member_user.id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member of this project")

    # Cannot add someone as owner (must transfer ownership)
    if data.role == ProjectRole.owner:
        raise HTTPException(status_code=400, detail="Cannot add member as owner. Use transfer ownership instead.")

    membership = ProjectMember(
        project_id=project_id,
        user_id=new_member_user.id,
        role=data.role,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)

    return ProjectMemberResponse(
        id=membership.id,
        user_id=membership.user_id,
        email=new_member_user.email,
        name=new_member_user.name,
        role=membership.role,
        created_at=membership.created_at,
    )


@router.put("/projects/{project_id}/members/{member_user_id}", response_model=ProjectMemberResponse)
async def update_project_member(
    project_id: UUID,
    member_user_id: UUID,
    data: ProjectMemberUpdate,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Update a member's role. Requires admin or owner role (user auth only)."""
    if isinstance(auth, str):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Managing project members requires user authentication. Please log in.",
        )

    user: User = auth
    project, current_membership = get_project_with_access(project_id, db, user, minimum_role=ProjectRole.admin)

    # Find the membership to update
    membership = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == member_user_id,
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Member not found")

    # Cannot change owner role (must transfer ownership)
    if membership.role == ProjectRole.owner:
        raise HTTPException(status_code=400, detail="Cannot change owner's role. Use transfer ownership instead.")

    # Cannot promote to owner
    if data.role == ProjectRole.owner:
        raise HTTPException(status_code=400, detail="Cannot promote to owner. Use transfer ownership instead.")

    # Admins cannot promote others to admin (only owners can)
    if current_membership.role == ProjectRole.admin and data.role == ProjectRole.admin:
        raise HTTPException(status_code=403, detail="Only owners can promote members to admin")

    membership.role = data.role
    db.commit()
    db.refresh(membership)

    member_user = db.query(User).filter(User.id == member_user_id).first()

    return ProjectMemberResponse(
        id=membership.id,
        user_id=membership.user_id,
        email=member_user.email,
        name=member_user.name,
        role=membership.role,
        created_at=membership.created_at,
    )


@router.delete("/projects/{project_id}/members/{member_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_member(
    project_id: UUID,
    member_user_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Remove a member from the project. Requires admin or owner role (user auth only)."""
    if isinstance(auth, str):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Managing project members requires user authentication. Please log in.",
        )

    user: User = auth
    project, current_membership = get_project_with_access(project_id, db, user, minimum_role=ProjectRole.admin)

    # Find the membership to remove
    membership = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == member_user_id,
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Member not found")

    # Cannot remove the owner
    if membership.role == ProjectRole.owner:
        raise HTTPException(status_code=400, detail="Cannot remove the project owner")

    # Admins cannot remove other admins (only owners can)
    if current_membership.role == ProjectRole.admin and membership.role == ProjectRole.admin:
        raise HTTPException(status_code=403, detail="Only owners can remove admins")

    db.delete(membership)
    db.commit()


@router.post("/projects/{project_id}/transfer-ownership", response_model=ProjectResponse)
async def transfer_project_ownership(
    project_id: UUID,
    new_owner_user_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Transfer project ownership to another member. Only the current owner can do this (user auth only)."""
    if isinstance(auth, str):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Transferring ownership requires user authentication. Please log in.",
        )

    user: User = auth
    project, current_membership = get_project_with_access(project_id, db, user, minimum_role=ProjectRole.owner)

    # Verify the user is actually the owner (not just admin)
    actual_membership = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user.id,
    ).first()
    if not actual_membership or actual_membership.role != ProjectRole.owner:
        raise HTTPException(status_code=403, detail="Only the project owner can transfer ownership")

    # Find the new owner's membership
    new_owner_membership = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == new_owner_user_id,
    ).first()
    if not new_owner_membership:
        raise HTTPException(status_code=404, detail="New owner must already be a member of the project")

    # Transfer ownership
    actual_membership.role = ProjectRole.admin
    new_owner_membership.role = ProjectRole.owner

    db.commit()
    db.refresh(project)

    return ProjectResponse(
        id=project.id,
        name=project.name,
        slug=project.slug,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        member_count=len(project.members),
        current_user_role=ProjectRole.admin,
    )
