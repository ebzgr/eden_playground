"""Command-line helpers for local development."""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from urllib.parse import quote

from playground.config import get_settings
from playground.db import async_session_factory, init_db
from playground.identity.service import hash_return_code, mint_return_code
from playground.models.user import User
from playground.seed import seed_database
from playground.services.player_state.service import set_state

VALID_ORB_IDS = frozenset(
    {"clarity", "presence", "wisdom", "resistance", "authenticity"}
)


async def _db_init() -> None:
    await init_db()
    await seed_database()


async def _create_test_user(
    *,
    orbs: list[str],
    base_url: str,
    consent: str,
) -> tuple[str, str]:
    await init_db()
    await seed_database()

    unknown = [o for o in orbs if o not in VALID_ORB_IDS]
    if unknown:
        raise SystemExit(
            f"Unknown orb id(s): {', '.join(unknown)}. "
            f"Valid: {', '.join(sorted(VALID_ORB_IDS))}"
        )

    return_code = mint_return_code()
    user_hash = hash_return_code(return_code)

    async with async_session_factory() as db:
        user = User(user_id_hash=user_hash, consent_state=consent)
        db.add(user)
        await db.flush()

        if orbs:
            await set_state(
                db,
                user,
                "journey.orbs",
                orbs,
                str(uuid.uuid4()),
                "map_world",
                "map",
            )

        await db.commit()
        user_id = str(user.id)

    path = (
        "/worlds/map_world/scenes/map/view"
        f"?return_code={quote(return_code, safe='')}"
    )
    link = f"{base_url.rstrip('/')}{path}"
    return return_code, link, user_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="playground",
        description="Eden Playground — local dev utilities",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    db_init = sub.add_parser(
        "db-init",
        help="Apply Alembic migrations and seed worlds/scenes from disk",
    )
    db_init.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Do not print the database path",
    )

    test_user = sub.add_parser(
        "create-test-user",
        help="Create a user with journey.orbs state and print a map test link",
    )
    test_user.add_argument(
        "--orbs",
        default="clarity,wisdom",
        help="Comma-separated orb ids stored in journey.orbs (default: clarity,wisdom)",
    )
    test_user.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Origin for the test link (default: http://localhost:8000)",
    )
    test_user.add_argument(
        "--consent",
        default="granted",
        choices=("granted", "pending", "denied"),
        help="User consent_state (default: granted)",
    )

    args = parser.parse_args(argv)

    if args.command == "db-init":
        asyncio.run(_db_init())
        if not args.quiet:
            db_path = get_settings().database_url.removeprefix("sqlite+aiosqlite:///")
            print(f"Database ready: {db_path}")
        print("Migrations applied; worlds synced; demo experiment ensured (if missing).")
        return 0

    if args.command == "create-test-user":
        orb_list = [o.strip() for o in args.orbs.split(",") if o.strip()]
        return_code, link, user_id = asyncio.run(
            _create_test_user(
                orbs=orb_list,
                base_url=args.base_url,
                consent=args.consent,
            )
        )
        print("Test user created.")
        print(f"  user_id:      {user_id}")
        print(f"  return_code:  {return_code}")
        print(f"  journey.orbs: {orb_list}")
        print(f"  consent:      {args.consent}")
        print()
        print("Open this link (sets cookie + localStorage, loads map with granted orbs):")
        print(link)
        return 0

    parser.error(f"unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
