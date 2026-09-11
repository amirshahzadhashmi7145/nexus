"""Shared FastAPI dependencies.

Learn: Depends(get_db) = FastAPI opens a DB session for the request, then closes it.
Routes stay thin; they ask for a session instead of creating engines themselves.
"""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
