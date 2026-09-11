"""API endpoint tests with an in-memory seeded NovaCart DB.

Learn: we override get_db so tests never need Docker Postgres.
Shared client fixture lives in conftest.py.
"""

from fastapi.testclient import TestClient


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
