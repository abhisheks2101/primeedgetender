"""Admin-only API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import require_admin
from app.models.user import User
from app.schemas.auth import MessageResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/status", response_model=MessageResponse)
def admin_status(
    current_admin: Annotated[User, Depends(require_admin)],
) -> MessageResponse:
    """Admin-only endpoint used to verify authorization rules."""
    return MessageResponse(message=f"Admin access granted for {current_admin.email}.")
