"""Management CLI for administrative tasks."""

from __future__ import annotations

import argparse
import getpass
import sys

from app.config import Settings
from app.core.database import create_db_engine, create_session_factory
from app.core.enums import UserRole
from app.core.security import validate_password_strength
from app.schemas.auth import UserCreate
from app.services.user_service import UserService


def create_admin(settings: Settings | None = None) -> int:
    settings = settings or Settings()
    engine = create_db_engine(settings)
    session_factory = create_session_factory(engine)

    with session_factory() as db:
        user_service = UserService(db)

        if user_service.admin_exists():
            print("An administrator account already exists. Aborting to prevent duplicates.", file=sys.stderr)
            return 1

        email = input("Admin email: ").strip()
        full_name = input("Admin full name: ").strip()
        password = getpass.getpass("Admin password: ")
        confirm_password = getpass.getpass("Confirm password: ")

        if not email or not full_name:
            print("Email and full name are required.", file=sys.stderr)
            return 1

        if password != confirm_password:
            print("Passwords do not match.", file=sys.stderr)
            return 1

        try:
            validate_password_strength(password)
            user = user_service.create_user(
                UserCreate(email=email, password=password, full_name=full_name),
                role=UserRole.ADMIN,
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1

        print(f"Administrator created successfully: {user.email}")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Tender Intelligence Platform management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("create-admin", help="Create the initial administrator account")

    args = parser.parse_args()

    if args.command == "create-admin":
        return create_admin()

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
