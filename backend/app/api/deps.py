"""API dependencies."""

from typing import Optional, Union
from uuid import UUID

from fastapi import Header, HTTPException, status, Depends, Request, Query
from sqlalchemy.orm import Session
import bcrypt

from app.database import get_db
from app.models import ApiKey, User, Project, ProjectMember, ProjectRole, UserRole


async def get_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> str:
    """
    Validate API key from header.

    For development, if no API keys exist in the database,
    any non-empty key is accepted (bootstrap mode).
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )

    # Check if any API keys exist (bootstrap mode)
    key_count = db.query(ApiKey).filter(ApiKey.active == True).count()

    if key_count == 0:
        # Bootstrap mode: accept any key for initial setup
        return x_api_key

    # Find key by prefix
    key_prefix = x_api_key[:8]
    api_key = db.query(ApiKey).filter(
        ApiKey.key_prefix == key_prefix,
        ApiKey.active == True,
    ).first()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Verify full key hash
    if not bcrypt.checkpw(x_api_key.encode(), api_key.key_hash.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Update last used timestamp
    from datetime import datetime
    api_key.last_used_at = datetime.utcnow()
    db.commit()

    return x_api_key


async def get_validated_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> Optional[ApiKey]:
    """
    Validate API key and return the ApiKey object (not just the string).
    Returns None if no API key provided, raises exception if invalid.
    """
    if not x_api_key:
        return None

    # Check if any API keys exist (bootstrap mode)
    key_count = db.query(ApiKey).filter(ApiKey.active == True).count()

    if key_count == 0:
        # Bootstrap mode: return None (no key object)
        return None

    # Find key by prefix
    key_prefix = x_api_key[:8]
    api_key = db.query(ApiKey).filter(
        ApiKey.key_prefix == key_prefix,
        ApiKey.active == True,
    ).first()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Verify full key hash
    if not bcrypt.checkpw(x_api_key.encode(), api_key.key_hash.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Update last used timestamp
    from datetime import datetime
    api_key.last_used_at = datetime.utcnow()
    db.commit()

    return api_key


async def get_api_key_or_user(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> Union[str, User]:
    """
    Validate either API key or user JWT token.

    This allows endpoints to accept both API key authentication
    (for CI/CD integration) and user authentication (for web UI).

    Returns:
        Either the API key string or the User object
    """
    # Try API key first if provided
    if x_api_key:
        return await get_api_key(x_api_key=x_api_key, db=db)

    # Try JWT token from cookie or Authorization header
    from app.core.security import get_token_from_request, verify_access_token

    token = get_token_from_request(request)
    if token:
        token_data = verify_access_token(token)
        if token_data:
            user = db.query(User).filter(User.id == token_data.user_id).first()
            if user and user.is_active:
                return user

    # Neither auth method succeeded
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="API key or valid session required",
    )


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from JWT token.

    This dependency requires a valid user session (JWT token),
    unlike get_api_key_or_user which also accepts API keys.

    Use this for endpoints that need user context (like projects).
    """
    from app.core.security import get_token_from_request, verify_access_token

    token = get_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    token_data = verify_access_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user


async def get_current_project(
    request: Request,
    x_project_id: Optional[str] = Header(None, alias="X-Project-Id"),
    project_id: Optional[UUID] = Query(None, description="Project ID (alternative to header)"),
    db: Session = Depends(get_db),
) -> Optional[Project]:
    """
    Get the current project from header or query parameter.

    Returns None if no project is specified (for backwards compatibility).
    Use get_required_project if project is mandatory.
    """
    pid = None
    if x_project_id:
        try:
            pid = UUID(x_project_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid project ID format",
            )
    elif project_id:
        pid = project_id

    if not pid:
        return None

    project = db.query(Project).filter(Project.id == pid).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project


async def get_required_project(
    project: Optional[Project] = Depends(get_current_project),
) -> Project:
    """
    Get the current project, raising an error if not specified.

    Use this for endpoints that require a project context.
    """
    if not project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project ID required. Provide X-Project-Id header or project_id query parameter.",
        )
    return project


async def get_project_for_user(
    request: Request,
    db: Session = Depends(get_db),
    project: Project = Depends(get_required_project),
    auth: Union[str, User] = Depends(get_api_key_or_user),
    api_key: Optional[ApiKey] = Depends(get_validated_api_key),
) -> Project:
    """
    Get current project and verify the user/API key has access.

    This combines authentication with project authorization.
    """
    # If authenticated via API key, check if key is scoped to this project
    if isinstance(auth, str):
        if api_key and api_key.project_id:
            # API key is scoped to a specific project
            if api_key.project_id != project.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="API key does not have access to this project",
                )
        # API key with no project_id has access to all projects (global key)
        return project

    # User auth - check project membership
    user: User = auth

    # Global admins have access to all projects
    if user.role == UserRole.admin:
        return project

    # Check membership
    membership = db.query(ProjectMember).filter(
        ProjectMember.project_id == project.id,
        ProjectMember.user_id == user.id,
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project",
        )

    return project


async def verify_project_access(
    request: Request,
    db: Session = Depends(get_db),
    project: Optional[Project] = Depends(get_current_project),
    auth: Union[str, User] = Depends(get_api_key_or_user),
    api_key: Optional[ApiKey] = Depends(get_validated_api_key),
) -> Optional[Project]:
    """
    Verify user/API key has access to the current project (if specified).

    Returns the project if access is granted, None if no project specified.
    Raises 403 if project specified but user doesn't have access.

    Use this for list endpoints where project filtering is optional.
    """
    if not project:
        return None

    # If authenticated via API key, check scope
    if isinstance(auth, str):
        if api_key and api_key.project_id:
            if api_key.project_id != project.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="API key does not have access to this project",
                )
        return project

    # User auth - check project membership
    user: User = auth

    # Global admins have access to all projects
    if user.role == UserRole.admin:
        return project

    # Check membership
    membership = db.query(ProjectMember).filter(
        ProjectMember.project_id == project.id,
        ProjectMember.user_id == user.id,
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project",
        )

    return project


def require_project_role(minimum_role: ProjectRole):
    """
    Dependency factory for role-based project access control.

    Usage:
        @router.post("/resource")
        async def create_resource(
            project: Project = Depends(require_project_role(ProjectRole.member)),
            ...
        ):
    """
    async def check_role(
        request: Request,
        db: Session = Depends(get_db),
        project: Project = Depends(get_required_project),
        user: User = Depends(get_current_user),
    ) -> Project:
        # Global admins bypass role checks
        if user.role == UserRole.admin:
            return project

        # Check membership and role
        membership = db.query(ProjectMember).filter(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user.id,
        ).first()

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this project",
            )

        # Check role hierarchy
        role_hierarchy = {
            ProjectRole.viewer: 0,
            ProjectRole.member: 1,
            ProjectRole.admin: 2,
            ProjectRole.owner: 3,
        }

        if role_hierarchy[membership.role] < role_hierarchy[minimum_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires at least {minimum_role.value} role",
            )

        return project

    return check_role


def get_user_project_role(
    db: Session,
    user: User,
    project: Project,
) -> Optional[ProjectRole]:
    """
    Get the user's role in a specific project.

    Returns None if user is not a member.
    Global admins are treated as having owner role in all projects.
    """
    if user.role == UserRole.admin:
        return ProjectRole.owner

    membership = db.query(ProjectMember).filter(
        ProjectMember.project_id == project.id,
        ProjectMember.user_id == user.id,
    ).first()

    return membership.role if membership else None


def can_write_to_project(
    db: Session,
    auth: Union[str, User, ApiKey],
    project: Optional[Project],
    api_key: Optional[ApiKey] = None,
) -> bool:
    """
    Check if the auth entity can write (create/update/delete) to a project.

    - API keys: can write if scoped to project or global
    - Users: can write if member role or higher
    """
    if not project:
        return True  # No project context = global operation allowed

    # API key auth
    if isinstance(auth, str):
        if api_key and api_key.project_id:
            return api_key.project_id == project.id
        return True  # Global API key can write anywhere

    # User auth
    user: User = auth
    role = get_user_project_role(db, user, project)

    if not role:
        return False

    # Viewers cannot write
    return role != ProjectRole.viewer
