import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Postgres in Docker for real work; local SQLite file for quick API demos.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+pysqlite:///../../data/novacart.db",
)


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
    return create_engine(db_url, future=True)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session():
    """FastAPI-style dependency placeholder for later phases."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
