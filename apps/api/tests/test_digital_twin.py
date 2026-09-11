from decimal import Decimal

from fastapi.testclient import TestClient


def test_digital_twin_snapshot(client: TestClient) -> None:
    response = client.get("/api/v1/digital-twin")
    assert response.status_code == 200
    body = response.json()

    assert body["organization"] == "NovaCart"
    assert body["customer_count"] == 10
    assert body["product_count"] == 8
    assert body["order_count"] == 12
    assert body["supplier_count"] == 3
    assert body["warehouse_count"] == 2
    assert Decimal(body["revenue"]) > 0
    assert Decimal(body["cogs"]) >= 0
    assert "profit" in body
    assert body["inventory_units"] > 0
    assert len(body["customers_by_segment"]) >= 1
    assert len(body["suppliers_by_reliability"]) >= 1


def test_digital_twin_is_reproducible_for_same_seed(client: TestClient) -> None:
    a = client.get("/api/v1/digital-twin").json()
    b = client.get("/api/v1/digital-twin").json()
    for key in (
        "revenue",
        "cogs",
        "profit",
        "inventory_units",
        "order_count",
        "customer_count",
        "product_count",
    ):
        assert a[key] == b[key]
