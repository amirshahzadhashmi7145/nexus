"""Lightweight agents for a pricing decision.

Mentor note: these are roles (functions), not ten chatbot personas.
Manager sequences work; specialists each own one concern.
"""

from __future__ import annotations

from app.llm.providers import StubProvider
from app.rag.retriever import retrieve
from app.schemas_decision import (
    CriticBrief,
    ResearchBrief,
    SimulationBrief,
    TwinBrief,
)
from app.schemas_twin import DigitalTwinOut
from app.services.simulation import PriceSimResult


def research_agent(*, question: str, top_k: int = 4) -> ResearchBrief:
    hits = retrieve(question, top_k=top_k)
    context = "\n\n".join(f"[{h.source}] {h.text}" for h in hits)
    # Reuse stub LLM shaping so research stays structured.
    analysis = StubProvider().analyze_policy(question=question, context=context)
    return ResearchBrief(
        findings=analysis.findings[:5],
        sources=sorted({h.source for h in hits}),
        context_excerpt=context[:1200],
    )


def twin_agent(twin: DigitalTwinOut) -> TwinBrief:
    return TwinBrief(
        revenue=float(twin.revenue),
        profit=float(twin.profit),
        inventory_units=twin.inventory_units,
        low_stock_skus=list(twin.low_stock_skus[:10]),
    )


def simulation_agent(result: PriceSimResult) -> SimulationBrief:
    return SimulationBrief(
        sku=result.sku,
        baseline_price=float(result.baseline_price),
        new_price=float(result.new_price),
        expected_revenue=result.expected_revenue,
        expected_profit=result.expected_profit,
        stockout_probability=result.stockout_probability,
        risk_note=result.risk_note,
    )


def critic_agent(
    *,
    research: ResearchBrief,
    twin: TwinBrief,
    simulation: SimulationBrief,
    price_change_pct: float,
) -> CriticBrief:
    risks: list[str] = []
    flags: list[str] = []
    missing: list[str] = []

    if simulation.stockout_probability >= 0.3:
        risks.append(
            f"High simulated stockout probability ({simulation.stockout_probability:.0%})."
        )
    elif simulation.stockout_probability >= 0.1:
        risks.append(
            f"Moderate stockout probability ({simulation.stockout_probability:.0%})."
        )

    if simulation.expected_profit < 0:
        risks.append("Expected profit is negative under this price change.")

    blob = " ".join(research.findings).lower() + " " + research.context_excerpt.lower()
    if "14" in blob and price_change_pct < 0:
        flags.append(
            "Policy mentions manager approval for promotions when coverage is below 14 days."
        )
    if abs(price_change_pct) > 15:
        flags.append("Price moves above 15% typically need executive approval.")
    elif abs(price_change_pct) > 5 and price_change_pct < 0:
        flags.append("Discounts between 5% and 15% typically need Finance review.")

    if simulation.sku in twin.low_stock_skus:
        risks.append(f"{simulation.sku} is already on the twin low-stock list.")

    if not research.sources:
        missing.append("No policy documents were retrieved for this question.")

    missing.append("Live supplier lead-time confirmation was not checked in this pass.")

    return CriticBrief(risks=risks, policy_flags=flags, missing_info=missing)


def manager_recommend(
    *,
    research: ResearchBrief,
    simulation: SimulationBrief,
    critic: CriticBrief,
    price_change_pct: float,
) -> tuple[str, str, list[str], float]:
    """Returns verdict, rationale, conditions, confidence."""
    conditions: list[str] = []
    hard_block = simulation.expected_profit < 0 and simulation.stockout_probability >= 0.3
    needs_guardrails = bool(critic.policy_flags) or simulation.stockout_probability >= 0.1

    if hard_block:
        return (
            "reject",
            "Simulation shows weak economics with elevated stockout risk.",
            ["Revisit price depth or replenish inventory before discounting."],
            0.55,
        )

    if needs_guardrails or abs(price_change_pct) > 5:
        if "Finance review" in " ".join(critic.policy_flags):
            conditions.append("Obtain Finance review before launch.")
        if "14 days" in " ".join(critic.policy_flags):
            conditions.append("Confirm inventory coverage ≥ 14 days or get manager approval.")
        if simulation.stockout_probability >= 0.1:
            conditions.append("Run replenishment plan or reduce discount depth.")
        if not conditions:
            conditions.append("Document assumptions and monitor sell-through daily.")
        return (
            "approve_with_conditions",
            "Potential upside exists, but policy/risk checks require controls.",
            conditions,
            0.7,
        )

    return (
        "approve",
        "Simulation and policy scan do not show major blockers for this modest change.",
        [],
        0.75,
    )
