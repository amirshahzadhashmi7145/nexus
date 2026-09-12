from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.data import GenerateConfig, generate_novacart
from app.db.base import Base
from app.db.session import make_engine
from app.main import app
from app.rag.retriever import build_index

DOCS = Path(__file__).resolve().parents[1] / "data" / "company"


def _client_with_db() -> tuple[TestClient, object]:
    engine = make_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as seed:
        generate_novacart(
            seed,
            GenerateConfig(seed=42, customers=8, products=5, orders=10, suppliers=2, warehouses=2),
        )

    def _override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = _override
    return TestClient(app), engine


def test_analyze_persists_pending_decision_and_audit() -> None:
    build_index(DOCS)
    client, _ = _client_with_db()
    try:
        response = client.post(
            "/api/v1/decisions/analyze-price-change",
            json={"sku": "P-0001", "price_change_pct": -10, "simulations": 20, "seed": 1},
        )
        assert response.status_code == 200
        decision_id = response.json()["decision_id"]

        stored = client.get(f"/api/v1/decisions/{decision_id}")
        assert stored.status_code == 200
        assert stored.json()["status"] == "pending"

        audit = client.get("/api/v1/audit")
        assert audit.status_code == 200
        actions = [item["action"] for item in audit.json()["items"]]
        assert "decision.created" in actions
    finally:
        app.dependency_overrides.clear()
        client.close()


def test_approve_and_reject_flow() -> None:
    build_index(DOCS)
    client, _ = _client_with_db()
    try:
        created = client.post(
            "/api/v1/decisions/analyze-price-change",
            json={"sku": "P-0001", "price_change_pct": -5, "simulations": 15, "seed": 2},
        ).json()
        decision_id = created["decision_id"]

        approved = client.post(
            f"/api/v1/decisions/{decision_id}/approve",
            json={"actor": "amir", "note": "Looks good"},
        )
        assert approved.status_code == 200
        body = approved.json()
        assert body["status"] == "approved"
        assert body["decided_by"] == "amir"

        again = client.post(
            f"/api/v1/decisions/{decision_id}/approve",
            json={"actor": "amir"},
        )
        assert again.status_code == 409

        other = client.post(
            "/api/v1/decisions/analyze-price-change",
            json={"sku": "P-0002", "price_change_pct": -8, "simulations": 15, "seed": 3},
        ).json()["decision_id"]
        rejected = client.post(
            f"/api/v1/decisions/{other}/reject",
            json={"actor": "amir", "note": "Stockout too high"},
        )
        assert rejected.status_code == 200
        assert rejected.json()["status"] == "rejected"
    finally:
        app.dependency_overrides.clear()
        client.close()
