"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import admin, auth, companies, health
from app.config import Settings, get_settings
from app.core.database import create_db_engine, create_session_factory
from app.logging_config import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    engine = create_db_engine(settings)
    session_factory = create_session_factory(engine)

    app.state.db_engine = engine
    app.state.db_session_factory = session_factory

    logger.info("Application startup complete", extra={"environment": settings.app_env})

    yield

    engine.dispose()
    logger.info("Application shutdown complete")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version or __version__,
        description="Tender Intelligence Platform API",
        docs_url="/api/docs" if settings.app_debug else None,
        redoc_url="/api/redoc" if settings.app_debug else None,
        openapi_url="/api/openapi.json" if settings.app_debug else None,
        lifespan=lifespan,
    )

    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(admin.router, prefix="/api")
    app.include_router(companies.router, prefix="/api")
    app.include_router(companies.documents_router, prefix="/api")

    return app


app = create_app()
