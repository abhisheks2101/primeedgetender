"""Authentication API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.core.deps import get_auth_service, require_authenticated_user
from app.models.user import User
from app.schemas.auth import MessageResponse, UserCreate, UserLogin, UserPublic
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserPublic:
    """Register a standard USER account when public registration is enabled."""
    return auth_service.register_user(payload)


@router.post("/login", response_model=UserPublic)
def login_user(
    payload: UserLogin,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserPublic:
    """Authenticate a user and establish a secure session cookie."""
    return auth_service.login(payload, response)


@router.post("/logout", response_model=MessageResponse)
def logout_user(
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    """Invalidate the current session and clear the authentication cookie."""
    auth_service.logout(response)
    return MessageResponse(message="Logged out successfully.")


@router.get("/me", response_model=UserPublic)
def get_current_user_profile(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserPublic:
    """Return the currently authenticated user."""
    return auth_service.get_current_user_public()


@router.get("/session-check", response_model=UserPublic)
def session_check(
    current_user: Annotated[User, Depends(require_authenticated_user)],
) -> UserPublic:
    """Authenticated endpoint available to both ADMIN and USER roles."""
    return UserPublic.model_validate(current_user)
