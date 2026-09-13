from fastapi.testclient import TestClient

from app.db.config import (
    DEFAULT_POSTGRES_URL,
    DEFAULT_SQLITE_URL,
    dialect_of,
    redact_database_url,
    resolve_database_url,
)


def test_resolve_defaults_to_sqlite(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("NEXUS_DB", raising=False)
    url = resolve_database_url()
    assert dialect_of(url) == "sqlite"
    assert url == DEFAULT_SQLITE_URL


def test_resolve_nexus_db_postgres(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("NEXUS_DB", "postgres")
    assert resolve_database_url() == DEFAULT_POSTGRES_URL


def test_resolve_explicit_database_url_wins(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://nexus:nexus@localhost:5432/nexus")
    monkeypatch.setenv("NEXUS_DB", "sqlite")
    assert "postgresql" in resolve_database_url()


def test_redact_password() -> None:
    redacted = redact_database_url("postgresql+psycopg://nexus:secret@localhost:5432/nexus")
    assert "secret" not in redacted
    assert "***" in redacted


def test_db_status_api(client: TestClient) -> None:
    response = client.get("/api/v1/db/status")
    assert response.status_code == 200
    body = response.json()
    assert "dialect" in body
    assert "url" in body
    assert "ok" in body
