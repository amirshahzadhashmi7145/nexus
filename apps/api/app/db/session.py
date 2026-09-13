import os

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.config import dialect_of, redact_database_url, resolve_database_url

# Resolved once at import. Restart uvicorn after changing DATABASE_URL / NEXUS_DB.
DATABASE_URL = resolve_database_url()


def make_engine(url: str | None = None):
    db_url = url or DATABASE_URL
    if db_url.startswith("sqlite"):
        # :memory: needs StaticPool so all sessions share one DB.
        if ":memory:" in db_url:
            return create_engine(
                db_url,
                future=True,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        return create_engine(db_url, future=True, connect_args={"check_same_thread": False})
    return create_engine(db_url, future=True, pool_pre_ping=True)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session():
    """FastAPI-style dependency placeholder for later phases."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def database_status() -> dict:
    """Lightweight DB probe for demos and debugging (no secrets)."""
    url = DATABASE_URL
    dialect = dialect_of(url)
    status: dict = {
        "dialect": dialect,
        "url": redact_database_url(url),
        "env_database_url_set": bool(os.getenv("DATABASE_URL", "").strip()),
        "nexus_db": os.getenv("NEXUS_DB", "sqlite"),
        "ok": False,
        "error": None,
        "counts": {},
    }
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            tables = ("products", "orders", "customers", "decision_runs")
            counts: dict[str, int | None] = {}
            for table in tables:
                try:
                    counts[table] = int(
                        conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0
                    )
                except SQLAlchemyError:
                    counts[table] = None
            status["counts"] = counts
            status["ok"] = True
    except SQLAlchemyError as exc:
        status["error"] = str(exc)
    return status
