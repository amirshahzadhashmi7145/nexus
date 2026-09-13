"""Pytest fixtures. Force in-memory SQLite before any app DB import."""

from __future__ import annotations

import os

# Must run before importing app.db.session / app.main (dotenv won't override).
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["NEXUS_DB"] = "sqlite"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.data import GenerateConfig, generate_novacart
from app.db.base import Base
from app.db.session import make_engine
from app.main import app


@pytest.fixture()
def client() -> TestClient:
    engine = make_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as seed_session:
        generate_novacart(
            seed_session,
            GenerateConfig(seed=42, customers=10, products=8, orders=12, suppliers=3, warehouses=2),
        )

    def _override_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
