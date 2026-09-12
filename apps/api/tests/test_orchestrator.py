from pathlib import Path

from fastapi.testclient import TestClient

from app.rag.retriever import build_index

DOCS = Path(__file__).resolve().parents[1] / "data" / "company"


def test_analyze_price_change_orchestrates_agents(client: TestClient) -> None:
    build_index(DOCS)
    response = client.post(
        "/api/v1/decisions/analyze-price-change",
        json={
            "sku": "P-0001",
            "price_change_pct": -10,
            "simulations": 40,
            "horizon_days": 30,
            "seed": 42,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["decision_id"].startswith("DEC-")
    assert len(body["plan"]) >= 5
    agents = [step["agent"] for step in body["agent_trace"]]
    assert agents[0] == "manager"
    assert "research" in agents
    assert "operations" in agents
    assert "finance" in agents
    assert "critic" in agents
    assert body["simulation"]["sku"] == "P-0001"
    assert body["digital_twin"]["organization"] == "NovaCart"
    assert body["policy"]["findings"]
    assert body["recommendation"]
    assert body["risks"]
    assert body["next_actions"]


def test_unknown_sku_in_decision_returns_404(client: TestClient) -> None:
    build_index(DOCS)
    response = client.post(
        "/api/v1/decisions/analyze-price-change",
        json={"sku": "NOPE", "price_change_pct": -5, "simulations": 20},
    )
    assert response.status_code == 404
