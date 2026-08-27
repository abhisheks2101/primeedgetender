"""User management service."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.security import hash_password, validate_password_strength
from app.models.user import User
from app.schemas.auth import UserCreate


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        normalized_email = email.strip().lower()
        return self.db.scalar(select(User).where(User.email == normalized_email))

    def get_by_id(self, user_id) -> User | None:
        return self.db.get(User, user_id)

    def email_exists(self, email: str) -> bool:
        return self.get_by_email(email) is not None

    def create_user(self, payload: UserCreate, role: UserRole = UserRole.USER) -> User:
        validate_password_strength(payload.password)
        normalized_email = payload.email.strip().lower()

        user = User(
            email=normalized_email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name.strip(),
            role=role,
            is_active=True,
        )
        self.db.add(user)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("A user with this email already exists.") from exc
        self.db.refresh(user)
        return user

    def admin_exists(self) -> bool:
        return self.db.scalar(select(User.id).where(User.role == UserRole.ADMIN).limit(1)) is not None
