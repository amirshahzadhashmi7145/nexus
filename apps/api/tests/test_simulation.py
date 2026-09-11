from decimal import Decimal

from fastapi.testclient import TestClient


def test_price_change_simulation_runs(client: TestClient) -> None:
    response = client.post(
        "/api/v1/simulations/price-change",
        json={
            "sku": "P-0001",
            "price_change_pct": -10,
            "simulations": 50,
            "horizon_days": 30,
            "seed": 42,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["sku"] == "P-0001"
    assert body["simulations"] == 50
    assert Decimal(str(body["new_price"])) < Decimal(str(body["baseline_price"]))
    assert 0 <= body["stockout_probability"] <= 1
    assert "risk_note" in body
    assert body["expected_revenue"] >= 0


def test_price_simulation_is_deterministic(client: TestClient) -> None:
    payload = {
        "sku": "P-0001",
        "price_change_pct": -10,
        "simulations": 40,
        "horizon_days": 30,
        "seed": 7,
    }
    a = client.post("/api/v1/simulations/price-change", json=payload).json()
    b = client.post("/api/v1/simulations/price-change", json=payload).json()
    assert a["expected_revenue"] == b["expected_revenue"]
    assert a["expected_profit"] == b["expected_profit"]
    assert a["stockout_probability"] == b["stockout_probability"]


def test_unknown_sku_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/simulations/price-change",
        json={"sku": "NOPE", "price_change_pct": -5, "simulations": 20},
    )
    assert response.status_code == 404


def test_discount_increases_expected_demand_vs_hike(client: TestClient) -> None:
    discount = client.post(
        "/api/v1/simulations/price-change",
        json={"sku": "P-0001", "price_change_pct": -20, "simulations": 80, "seed": 1},
    ).json()
    hike = client.post(
        "/api/v1/simulations/price-change",
        json={"sku": "P-0001", "price_change_pct": 20, "simulations": 80, "seed": 1},
    ).json()
    # With negative elasticity, a discount should sell at least as many units in expectation
    # (revenue can go either way; stockout risk often rises with discounts).
    assert discount["stockout_probability"] >= hike["stockout_probability"]
