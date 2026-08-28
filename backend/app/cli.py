"""Management CLI for administrative tasks."""

from __future__ import annotations

import argparse
import asyncio
import getpass
import sys
import time

from app.config import Settings
from app.core.database import create_db_engine, create_session_factory
from app.core.enums import UserRole
from app.core.security import validate_password_strength
from app.schemas.auth import UserCreate
from app.seed_companies import seed_demo_companies
from app.seed_tender_sources import seed_demo_tender_sources
from app.services.collection_runner import CollectionRunner
from app.services.tender_service import TenderService
from app.services.tender_source_service import TenderSourceService
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


async def collect_source_tenders(source_code: str, label: str, settings: Settings | None = None) -> int:
    settings = settings or Settings()
    engine = create_db_engine(settings)
    session_factory = create_session_factory(engine)

    with session_factory() as db:
        source_service = TenderSourceService(db)
        source = source_service.get_by_code(source_code)
        if source is None:
            print(f"{source_code} source is not configured. Run seed-tender-sources first.", file=sys.stderr)
            return 1
        if not source.is_active:
            print(f"{source_code} source is inactive.", file=sys.stderr)
            return 1

        started = time.perf_counter()
        runner = CollectionRunner(db)
        job = await runner.run_for_source(source.id)
        elapsed = round(time.perf_counter() - started, 2)

        print(f"{label} manual collection finished")
        print(f"  Job ID: {job.id}")
        print(f"  Status: {job.status.value}")
        print(f"  Discovered: {job.records_discovered}")
        print(f"  Processed: {job.records_processed}")
        print(f"  Created: {job.records_created}")
        print(f"  Updated: {job.records_updated}")
        print(f"  Skipped: {job.records_skipped}")
        print(f"  Failed: {job.records_failed}")
        print(f"  Duration: {elapsed}s")
        if job.error_message:
            print(f"  Error: {job.error_message}")
        return 0 if job.status.value in {"COMPLETED", "PARTIAL"} else 1


async def collect_up_tenders(settings: Settings | None = None) -> int:
    return await collect_source_tenders("UP_TENDER", "UP", settings)


async def collect_mp_tenders(settings: Settings | None = None) -> int:
    return await collect_source_tenders("MP_TENDER", "MP", settings)


def reprocess_normalization(
    settings: Settings | None = None,
    *,
    source_code: str | None = None,
    limit: int = 500,
) -> int:
    settings = settings or Settings()
    engine = create_db_engine(settings)
    session_factory = create_session_factory(engine)

    with session_factory() as db:
        source_service = TenderSourceService(db)
        tender_service = TenderService(db)
        sources = source_service.list_sources(active_only=False)
        if source_code:
            sources = [source for source in sources if source.code == source_code]
            if not sources:
                print(f"No tender source found for code {source_code}.", file=sys.stderr)
                return 1

        total = 0
        for source in sources:
            processed = tender_service.reprocess_all_for_source(
                source.id,
                source_code=source.code,
                limit=limit,
            )
            db.commit()
            total += processed
            print(f"  {source.code}: reprocessed {processed} tender(s)")

        print(f"Normalization reprocessing finished ({total} tender(s) total).")
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
    subparsers.add_parser(
        "collect-up",
        help="Manually collect tenders from the live UP portal (not for automated CI)",
    )

    subparsers.add_parser(
        "collect-mp",
        help="Manually collect tenders from the live MP portal (not for automated CI)",
    )
    reprocess_parser = subparsers.add_parser(
        "reprocess-normalization",
        help="Re-run normalization against stored raw tender payloads",
    )
    reprocess_parser.add_argument("--source-code", help="Limit reprocessing to one source code")
    reprocess_parser.add_argument("--limit", type=int, default=500, help="Maximum tenders per source")

    args = parser.parse_args()

    if args.command == "create-admin":
        return create_admin(email=args.email, full_name=getattr(args, "full_name", None), password=args.password)

    if args.command == "seed-companies":
        return seed_demo_companies()

    if args.command == "seed-tender-sources":
        return seed_demo_tender_sources()

    if args.command == "collect-up":
        return asyncio.run(collect_up_tenders())

    if args.command == "collect-mp":
        return asyncio.run(collect_mp_tenders())

    if args.command == "reprocess-normalization":
        return reprocess_normalization(source_code=getattr(args, "source_code", None), limit=args.limit)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
