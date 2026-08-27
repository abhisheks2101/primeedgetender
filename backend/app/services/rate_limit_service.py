"""Login rate limiting backed by PostgreSQL."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.user import LoginAttempt


class RateLimitService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    def is_login_blocked(self, email: str, ip_address: str | None) -> bool:
        window_start = datetime.now(timezone.utc) - timedelta(
            minutes=self.settings.login_rate_limit_window_minutes
        )
        normalized_email = email.strip().lower()

        failed_attempts = self.db.scalar(
            select(func.count(LoginAttempt.id)).where(
                LoginAttempt.email == normalized_email,
                LoginAttempt.successful.is_(False),
                LoginAttempt.attempted_at >= window_start,
            )
        )
        return (failed_attempts or 0) >= self.settings.login_rate_limit_max_attempts

    def record_attempt(self, email: str, ip_address: str | None, successful: bool) -> None:
        attempt = LoginAttempt(
            email=email.strip().lower(),
            ip_address=ip_address,
            successful=successful,
        )
        self.db.add(attempt)
        self.db.commit()
