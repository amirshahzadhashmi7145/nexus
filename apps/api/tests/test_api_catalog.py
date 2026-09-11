"""API endpoint tests with an in-memory seeded NovaCart DB.

Learn: we override get_db so tests never need Docker Postgres.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.data import GenerateConfig, generate_novacart
from app.db.base import Base
from app.db.session import make_engine
from app.main import app
from app.api.deps import get_db


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


def test_list_products(client: TestClient) -> None:
    response = client.get("/api/v1/products?limit=5")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 5
    assert body["items"][0]["sku"].startswith("P-")


def test_get_product_by_sku(client: TestClient) -> None:
    response = client.get("/api/v1/products/P-0001")
    assert response.status_code == 200
    assert response.json()["sku"] == "P-0001"


def test_get_product_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/products/NOPE")
    assert response.status_code == 404


def test_list_inventory(client: TestClient) -> None:
    response = client.get("/api/v1/inventory?limit=10")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 10
    assert body["items"][0]["sku"] is not None
    assert body["items"][0]["warehouse_external_id"] is not None


def test_list_orders_and_detail(client: TestClient) -> None:
    listing = client.get("/api/v1/orders?limit=3")
    assert listing.status_code == 200
    items = listing.json()["items"]
    assert len(items) == 3
    external_id = items[0]["external_id"]

    detail = client.get(f"/api/v1/orders/{external_id}")
    assert detail.status_code == 200
    assert detail.json()["external_id"] == external_id
    assert len(detail.json()["items"]) >= 1
