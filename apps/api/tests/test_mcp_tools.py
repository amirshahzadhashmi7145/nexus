"""Tests for MCP tool functions (call tools without stdio host)."""

from pathlib import Path

from app.mcp_server import (
    analyze_price_decision,
    ask_policy_question,
    get_digital_twin,
    mcp,
    search_policies,
    simulate_sku_price_change,
)
from app.rag.retriever import build_index

DOCS = Path(__file__).resolve().parents[1] / "data" / "company"


def test_mcp_registers_expected_tools() -> None:
    names = sorted(tool.name for tool in mcp._tool_manager.list_tools())
    assert "get_digital_twin" in names
    assert "search_policies" in names
    assert "ask_policy_question" in names
    assert "simulate_sku_price_change" in names
    assert "analyze_price_decision" in names


def test_mcp_get_digital_twin_tool() -> None:
    # Uses configured DATABASE_URL (sqlite novacart by default if seeded).
    # For unit safety we only assert shape when DB has data; otherwise skip soft.
    twin = get_digital_twin()
    assert "organization" in twin
    assert twin["organization"] == "NovaCart"


def test_mcp_search_and_policy_tools() -> None:
    build_index(DOCS)
    hits = search_policies("14 days coverage promotion approval", top_k=2)
    assert hits["hits"]
    answer = ask_policy_question("Do promos need approval under 14 days coverage?")
    assert answer["analysis"]["findings"]


def test_mcp_simulate_and_orchestrate(monkeypatch, tmp_path) -> None:
    # Use in-memory DB for isolation
    from app.db.base import Base
    from app.db import session as session_mod
    from app.data import GenerateConfig, generate_novacart
    from sqlalchemy.orm import sessionmaker

    engine = session_mod.make_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, future=True
    )

    with TestingSession() as db:
        generate_novacart(
            db,
            GenerateConfig(seed=42, customers=8, products=5, orders=10, suppliers=2, warehouses=2),
        )

    monkeypatch.setattr("app.mcp_server.SessionLocal", TestingSession)
    build_index(DOCS)

    sim = simulate_sku_price_change("P-0001", -10, simulations=20, seed=1)
    assert sim["sku"] == "P-0001"
    assert "expected_profit" in sim

    decision = analyze_price_decision("P-0001", -10, simulations=20, seed=1)
    assert decision["decision_id"].startswith("DEC-")
    assert decision["agent_trace"]
