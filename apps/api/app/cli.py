"""CLI entrypoints for local NovaCart workflows.

Usage (from apps/api):
  PYTHONPATH=. python -m app.cli generate-data --seed 42
  PYTHONPATH=. python -m app.cli db-status
"""

from __future__ import annotations

import argparse
import json

from app.data import GenerateConfig, generate_novacart, validate_novacart
from app.db.base import Base
from app.db.config import dialect_of, redact_database_url, resolve_database_url
from app.db.session import database_status, make_engine
from sqlalchemy.orm import Session


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nexus-api", description="NEXUS API utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate-data", help="Generate deterministic NovaCart seed data")
    gen.add_argument("--seed", type=int, default=42)
    gen.add_argument("--customers", type=int, default=100)
    gen.add_argument("--products", type=int, default=50)
    gen.add_argument("--orders", type=int, default=500)
    gen.add_argument("--suppliers", type=int, default=8)
    gen.add_argument("--warehouses", type=int, default=3)
    gen.add_argument(
        "--database-url",
        default=None,
        help="SQLAlchemy URL (default: resolve DATABASE_URL / NEXUS_DB / sqlite file)",
    )

    sub.add_parser("db-status", help="Show which database the CLI/API config points at")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "db-status":
        # Prefer live probe via session helpers when using process defaults;
        # if -- not applicable, still print resolved URL.
        url = resolve_database_url()
        print(json.dumps({"resolved_url": redact_database_url(url), "dialect": dialect_of(url)}, indent=2))
        print(json.dumps(database_status(), indent=2))
        return 0

    if args.command == "generate-data":
        url = resolve_database_url(args.database_url)
        print(f"Seeding dialect={dialect_of(url)} url={redact_database_url(url)}")
        engine = make_engine(url)
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            result = generate_novacart(
                session,
                GenerateConfig(
                    seed=args.seed,
                    customers=args.customers,
                    products=args.products,
                    orders=args.orders,
                    suppliers=args.suppliers,
                    warehouses=args.warehouses,
                ),
            )
            issues = validate_novacart(session)

        print("Generated:", result)
        if issues:
            print("Validation FAILED:")
            for issue in issues:
                print(f"  - [{issue.code}] {issue.message}")
            return 1
        print("Validation: OK")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
