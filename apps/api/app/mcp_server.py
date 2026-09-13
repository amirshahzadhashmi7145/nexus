"""NEXUS MCP server — expose NovaCart tools to LLM hosts.

Mentor:
- MCP = Model Context Protocol: a standard way for an AI host (Cursor, Claude, etc.)
  to discover and call *your* tools.
- Tools here wrap the same services the REST API uses (twin, RAG, sim, orchestrator).
- Default transport is stdio (host spawns this process and talks over stdin/stdout).

Run (from apps/api, with venv + PYTHONPATH=.):
  python -m app.mcp_server
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.rag.retriever import get_index, retrieve
from app.schemas_decision import PriceDecisionIn
from app.services.approvals import resolve_decision, save_price_decision
from app.services.digital_twin import build_digital_twin
from app.services.orchestrator import analyze_price_decision as run_price_decision
from app.services.policy_qa import answer_policy_question
from app.services.simulation import PriceSimRequest, simulate_price_change

mcp = FastMCP("nexus-novacart")
Base.metadata.create_all(bind=engine)


def _session() -> Session:
    return SessionLocal()


@mcp.tool()
def get_digital_twin() -> dict:
    """Return the current NovaCart digital-twin snapshot (derived metrics)."""
    with _session() as db:
        twin = build_digital_twin(db)
    return twin.model_dump(mode="json")


@mcp.tool()
def search_policies(question: str, top_k: int = 3) -> dict:
    """Retrieve relevant NovaCart policy chunks for a question (RAG, no LLM answer)."""
    get_index()
    hits = retrieve(question, top_k=top_k)
    return {
        "question": question,
        "hits": [
            {
                "source": h.source,
                "chunk_id": h.chunk_id,
                "score": round(h.score, 4),
                "text": h.text,
            }
            for h in hits
        ],
    }


@mcp.tool()
def ask_policy_question(question: str, top_k: int = 4) -> dict:
    """RAG + structured policy analysis (LLM_PROVIDER env; default stub)."""
    get_index()
    result = answer_policy_question(question=question, top_k=top_k)
    return result.model_dump(mode="json")


@mcp.tool()
def simulate_sku_price_change(
    sku: str,
    price_change_pct: float,
    simulations: int = 100,
    horizon_days: int = 30,
    seed: int = 42,
) -> dict:
    """Run Monte Carlo price-change simulation for one SKU."""
    with _session() as db:
        result = simulate_price_change(
            db,
            PriceSimRequest(
                sku=sku,
                price_change_pct=price_change_pct,
                simulations=simulations,
                horizon_days=horizon_days,
                seed=seed,
            ),
        )
    return {
        "sku": result.sku,
        "baseline_price": str(result.baseline_price),
        "new_price": str(result.new_price),
        "expected_revenue": result.expected_revenue,
        "expected_profit": result.expected_profit,
        "stockout_probability": result.stockout_probability,
        "risk_note": result.risk_note,
        "simulations": result.simulations,
        "horizon_days": result.horizon_days,
    }


@mcp.tool()
def analyze_price_decision(
    sku: str,
    price_change_pct: float,
    simulations: int = 100,
    horizon_days: int = 30,
    seed: int = 42,
) -> dict:
    """Full manager orchestrator; also persists a pending decision for human approval."""
    get_index()
    body = PriceDecisionIn(
        sku=sku,
        price_change_pct=price_change_pct,
        simulations=simulations,
        horizon_days=horizon_days,
        seed=seed,
    )
    with _session() as db:
        result = run_price_decision(db, body)
        save_price_decision(db, result)
    return result.model_dump(mode="json")


@mcp.tool()
def approve_decision(decision_id: str, actor: str = "human", note: str | None = None) -> dict:
    """Human-approve a pending decision and write an audit event."""
    with _session() as db:
        row = resolve_decision(
            db, decision_id=decision_id, approve=True, actor=actor, note=note
        )
    return {
        "decision_id": row.decision_id,
        "status": row.status,
        "decided_by": row.decided_by,
        "decision_note": row.decision_note,
    }


@mcp.tool()
def reject_decision(decision_id: str, actor: str = "human", note: str | None = None) -> dict:
    """Human-reject a pending decision and write an audit event."""
    with _session() as db:
        row = resolve_decision(
            db, decision_id=decision_id, approve=False, actor=actor, note=note
        )
    return {
        "decision_id": row.decision_id,
        "status": row.status,
        "decided_by": row.decided_by,
        "decision_note": row.decision_note,
    }


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
