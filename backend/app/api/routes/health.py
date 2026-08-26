"""Health check endpoints."""

import logging
from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


class DatabaseHealth(BaseModel):
    status: Literal["connected", "disconnected"]
    latency_ms: float | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    application: str
    version: str
    environment: str
    database: DatabaseHealth


@router.get("/health", response_model=HealthResponse)
def health_check(request: Request) -> HealthResponse:
    """Return application and database health information."""
    settings = request.app.state.settings
    engine: Engine = request.app.state.db_engine

    from app.core.database import check_database_connection

    is_connected, latency_ms, error = check_database_connection(engine)

    if is_connected:
        db_health = DatabaseHealth(status="connected", latency_ms=latency_ms)
        overall_status: Literal["healthy", "degraded", "unhealthy"] = "healthy"
    else:
        db_health = DatabaseHealth(status="disconnected", error=error)
        overall_status = "unhealthy"

    logger.info(
        "Health check completed",
        extra={"status": overall_status, "database_status": db_health.status},
    )

    return HealthResponse(
        status=overall_status,
        application=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        database=db_health,
    )
