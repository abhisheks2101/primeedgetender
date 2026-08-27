"""Authentication and session management."""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.core.enums import UserRole
from app.core.security import (
    generate_session_token,
    hash_session_token,
    validate_password_strength,
    verify_password,
)
from app.models.user import User, UserSession
from app.schemas.auth import UserCreate, UserLogin, UserPublic
from app.services.rate_limit_service import RateLimitService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

INVALID_CREDENTIALS_MESSAGE = "Invalid email or password."


class AuthService:
    def __init__(self, db: Session, settings: Settings, request: Request):
        self.db = db
        self.settings = settings
        self.request = request
        self.user_service = UserService(db)
        self.rate_limit_service = RateLimitService(db, settings)

    def register_user(self, payload: UserCreate) -> UserPublic:
        if not self.settings.allow_public_registration:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Public registration is disabled.",
            )

        try:
            user = self.user_service.create_user(payload, role=UserRole.USER)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        logger.info("Registered new user", extra={"user_id": str(user.id), "role": user.role.value})
        return UserPublic.model_validate(user)

    def login(self, payload: UserLogin, response: Response) -> UserPublic:
        normalized_email = payload.email.strip().lower()
        client_ip = self.request.client.host if self.request.client else None

        if self.rate_limit_service.is_login_blocked(normalized_email, client_ip):
            logger.warning("Login blocked due to rate limit", extra={"email": normalized_email})
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Please try again later.",
            )

        user = self.user_service.get_by_email(normalized_email)
        if user is None or not verify_password(payload.password, user.password_hash):
            self.rate_limit_service.record_attempt(normalized_email, client_ip, successful=False)
            logger.info("Failed login attempt", extra={"email": normalized_email})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=INVALID_CREDENTIALS_MESSAGE,
            )

        if not user.is_active:
            self.rate_limit_service.record_attempt(normalized_email, client_ip, successful=False)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=INVALID_CREDENTIALS_MESSAGE,
            )

        self.rate_limit_service.record_attempt(normalized_email, client_ip, successful=True)
        user.last_login_at = datetime.now(timezone.utc)
        session_token = self._create_session(user)
        self._set_session_cookie(response, session_token)
        self.db.commit()
        self.db.refresh(user)

        logger.info("User logged in", extra={"user_id": str(user.id), "role": user.role.value})
        return UserPublic.model_validate(user)

    def logout(self, response: Response) -> None:
        token = self.request.cookies.get(self.settings.session_cookie_name)
        if token:
            token_hash = hash_session_token(token)
            self.db.execute(delete(UserSession).where(UserSession.token_hash == token_hash))
            self.db.commit()
        self._clear_session_cookie(response)
        logger.info("User logged out")

    def get_current_user(self) -> User | None:
        token = self.request.cookies.get(self.settings.session_cookie_name)
        if not token:
            return None

        token_hash = hash_session_token(token)
        now = datetime.now(timezone.utc)

        session = self.db.scalar(
            select(UserSession)
            .where(UserSession.token_hash == token_hash, UserSession.expires_at > now)
        )
        if session is None:
            return None

        user = self.user_service.get_by_id(session.user_id)
        if user is None or not user.is_active:
            return None
        return user

    def get_current_user_public(self) -> UserPublic:
        user = self.get_current_user()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required.",
            )
        return UserPublic.model_validate(user)

    def _create_session(self, user: User) -> str:
        token = generate_session_token()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=self.settings.session_expire_hours)
        session = UserSession(
            user_id=user.id,
            token_hash=hash_session_token(token),
            expires_at=expires_at,
        )
        self.db.add(session)
        return token

    def _set_session_cookie(self, response: Response, token: str) -> None:
        response.set_cookie(
            key=self.settings.session_cookie_name,
            value=token,
            httponly=True,
            secure=self.settings.cookie_secure,
            samesite=self.settings.cookie_samesite,
            max_age=self.settings.session_expire_hours * 3600,
            path="/",
        )

    def _clear_session_cookie(self, response: Response) -> None:
        response.delete_cookie(
            key=self.settings.session_cookie_name,
            path="/",
            httponly=True,
            secure=self.settings.cookie_secure,
            samesite=self.settings.cookie_samesite,
        )

    @staticmethod
    def validate_registration_payload(payload: UserCreate) -> None:
        validate_password_strength(payload.password)
