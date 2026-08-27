"""Business logic for tender source management."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import SourceHealthStatus
from app.models.tender_source import TenderSource
from app.schemas.tender_source import (
    SourceConfiguration,
    TenderSourceCreate,
    TenderSourceStatusUpdate,
    TenderSourceUpdate,
)


class TenderSourceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_sources(
        self,
        *,
        active_only: bool | None = None,
        state: str | None = None,
    ) -> list[TenderSource]:
        query = select(TenderSource).order_by(TenderSource.priority.asc(), TenderSource.name.asc())
        if active_only is not None:
            query = query.where(TenderSource.is_active.is_(active_only))
        if state:
            query = query.where(TenderSource.state == state)
        return list(self.db.scalars(query).all())

    def get_source_or_404(self, source_id: UUID) -> TenderSource:
        source = self.db.get(TenderSource, source_id)
        if source is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender source not found.")
        return source

    def create_source(self, payload: TenderSourceCreate) -> TenderSource:
        source = TenderSource(
            name=payload.name,
            code=payload.code,
            state=payload.state,
            authority=payload.authority,
            portal_url=str(payload.portal_url) if payload.portal_url else None,
            source_type=payload.source_type,
            collection_method=payload.collection_method,
            is_active=payload.is_active,
            priority=payload.priority,
            description=payload.description,
            configuration=payload.configuration.model_dump(mode="json"),
            health_status=SourceHealthStatus.UNKNOWN,
        )
        self.db.add(source)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A tender source with this code already exists.",
            ) from exc
        self.db.refresh(source)
        return source

    def update_source(self, source_id: UUID, payload: TenderSourceUpdate) -> TenderSource:
        source = self.get_source_or_404(source_id)
        updates = payload.model_dump(exclude_unset=True)

        if "portal_url" in updates:
            portal_url = updates.pop("portal_url")
            source.portal_url = str(portal_url) if portal_url else None
        if "configuration" in updates:
            configuration = updates.pop("configuration")
            source.configuration = configuration.model_dump(mode="json") if configuration else {}

        for field, value in updates.items():
            setattr(source, field, value)

        self.db.commit()
        self.db.refresh(source)
        return source

    def update_status(self, source_id: UUID, payload: TenderSourceStatusUpdate) -> TenderSource:
        source = self.get_source_or_404(source_id)
        source.is_active = payload.is_active
        if payload.health_status is not None:
            source.health_status = payload.health_status
        self.db.commit()
        self.db.refresh(source)
        return source

    @staticmethod
    def parse_configuration(source: TenderSource) -> SourceConfiguration:
        return SourceConfiguration.model_validate(source.configuration or {})
