"""Database URL resolution.

Learn:
- Postgres (Docker Compose) is the business source of truth for demos that mirror prod.
- SQLite file remains the zero-setup fallback for quick laptop work.
- Tests always pass an explicit in-memory SQLite URL and ignore this default.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse

# apps/api/app/db/config.py → repo root is parents[4]
REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SQLITE_PATH = REPO_ROOT / "data" / "novacart.db"
DEFAULT_SQLITE_URL = f"sqlite+pysqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"
DEFAULT_POSTGRES_URL = "postgresql+psycopg://nexus:nexus@localhost:5432/nexus"


def load_dotenv_if_present() -> None:
    """Load repo-root .env once if python-dotenv is installed (optional)."""
    if os.getenv("NEXUS_SKIP_DOTENV") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
        return
    env_path = REPO_ROOT / ".env"
    if not env_path.is_file():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(env_path, override=False)


def resolve_database_url(explicit: str | None = None) -> str:
    """Pick DATABASE_URL, or NEXUS_DB=postgres|sqlite, else SQLite file."""
    load_dotenv_if_present()
    if explicit:
        return explicit.strip()

    from_env = os.getenv("DATABASE_URL", "").strip()
    if from_env:
        return from_env

    mode = os.getenv("NEXUS_DB", "sqlite").strip().lower()
    if mode in {"postgres", "postgresql", "pg"}:
        return DEFAULT_POSTGRES_URL
    return DEFAULT_SQLITE_URL


def dialect_of(url: str) -> str:
    if url.startswith("sqlite"):
        return "sqlite"
    if url.startswith("postgresql") or url.startswith("postgres"):
        return "postgresql"
    return urlparse(url).scheme or "unknown"


def redact_database_url(url: str) -> str:
    """Hide password in status output."""
    parsed = urlparse(url)
    if not parsed.password:
        return url
    netloc = parsed.netloc
    # user:password@host → user:***@host
    if "@" in netloc and ":" in netloc.split("@", 1)[0]:
        userinfo, hostinfo = netloc.rsplit("@", 1)
        user = userinfo.split(":", 1)[0]
        netloc = f"{user}:***@{hostinfo}"
    return urlunparse(parsed._replace(netloc=netloc))
