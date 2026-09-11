import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Postgres in Docker for real work; SQLite for fast local/model tests.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://nexus:nexus@localhost:5432/nexus",
)


def make_engine(url: str | None = None):
    db_url = url or DATABASE_URL
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    return create_engine(db_url, future=True, connect_args=connect_args)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session():
    """FastAPI-style dependency placeholder for later phases."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
