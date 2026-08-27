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
from app.seed_companies import seed_demo_companies
from app.seed_tender_sources import seed_demo_tender_sources
from app.services.user_service import UserService


def create_admin(
    settings: Settings | None = None,
    email: str | None = None,
    full_name: str | None = None,
    password: str | None = None,
) -> int:
    settings = settings or Settings()
    engine = create_db_engine(settings)
    session_factory = create_session_factory(engine)

    with session_factory() as db:
        user_service = UserService(db)

        if email:
            existing = user_service.get_by_email(email)
            if existing:
                if existing.role == UserRole.ADMIN:
                    print(f"Administrator already exists: {existing.email}")
                    return 0
                print("A non-admin user already exists with this email.", file=sys.stderr)
                return 1
        elif user_service.admin_exists():
            print("An administrator account already exists. Aborting to prevent duplicates.", file=sys.stderr)
            return 1

        if not email:
            email = input("Admin email: ").strip()
        if not full_name:
            full_name = input("Admin full name: ").strip()
        if not password:
            password = getpass.getpass("Admin password: ")
            confirm_password = getpass.getpass("Confirm password: ")
            if password != confirm_password:
                print("Passwords do not match.", file=sys.stderr)
                return 1

        if not email or not full_name or not password:
            print("Email, full name, and password are required.", file=sys.stderr)
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

    create_admin_parser = subparsers.add_parser("create-admin", help="Create the initial administrator account")
    create_admin_parser.add_argument("--email")
    create_admin_parser.add_argument("--full-name")
    create_admin_parser.add_argument("--password")
    subparsers.add_parser("seed-companies", help="Seed fictional development/demo company data")
    subparsers.add_parser("seed-tender-sources", help="Seed fictional development/demo tender sources")

    args = parser.parse_args()

    if args.command == "create-admin":
        return create_admin(email=args.email, full_name=getattr(args, "full_name", None), password=args.password)

    if args.command == "seed-companies":
        return seed_demo_companies()

    if args.command == "seed-tender-sources":
        return seed_demo_tender_sources()

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
