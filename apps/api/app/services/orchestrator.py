"""Manager-orchestrated pricing decision (lightweight multi-agent).

Flow:
  Manager plans
    → Research (RAG + structured policy analysis)
    → Operations (digital twin snapshot)
    → Finance/Sim (Monte Carlo price change)
    → Critic (policy vs risk checks)
    → Manager recommendation

Research uses get_provider() (stub by default; openai_compatible / vllm via env).
Other agents stay deterministic functions so CPU demos stay reliable.
"""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from app.llm.providers import get_provider
from app.rag.retriever import retrieve
from app.schemas_decision import AgentStep, PriceDecisionIn, PriceDecisionOut
from app.schemas_simulation import PriceSimulationOut
from app.services.digital_twin import build_digital_twin
from app.services.simulation import PriceSimRequest, simulate_price_change


def analyze_price_decision(db: Session, body: PriceDecisionIn) -> PriceDecisionOut:
    decision_id = f"DEC-{uuid4().hex[:8].upper()}"
    question = (
        f"Should NovaCart change price of {body.sku} by {body.price_change_pct}% "
        f"over the next {body.horizon_days} days?"
    )
    plan = [
        "Clarify pricing decision and SKU",
        "Research relevant pricing/inventory/marketing policies",
        "Inspect current digital-twin business state",
        "Simulate price change outcomes (Monte Carlo)",
        "Critique risks and policy conflicts",
        "Recommend approve or reject with next actions",
    ]
    trace: list[AgentStep] = [
        AgentStep(
            agent="manager",
            role="Plan the analysis",
            summary="Created a 6-step decision plan for the pricing question.",
        )
    ]

    # --- Research agent ---
    policy_question = (
        f"For a {body.price_change_pct}% price change and possible promotion on {body.sku}, "
        "what approval rules, coverage limits, and margin constraints apply?"
    )
    hits = retrieve(policy_question, top_k=body.top_k_policies)
    context = "\n\n".join(f"[{h.source}] {h.text}" for h in hits) or "No policy context."
    llm = get_provider(body.provider)
    policy = llm.analyze_policy(question=policy_question, context=context)
    trace.append(
        AgentStep(
            agent="research",
            role=f"Retrieve and interpret company policies ({llm.name})",
            summary=policy.answer_summary,
        )
    )

    # --- Operations agent ---
    twin = build_digital_twin(db)
    trace.append(
        AgentStep(
            agent="operations",
            role="Summarize current digital twin state",
            summary=(
                f"Twin snapshot: revenue={twin.revenue}, profit={twin.profit}, "
                f"inventory_units={twin.inventory_units}, low_stock={len(twin.low_stock_skus)} SKUs."
            ),
        )
    )

    # --- Finance / simulation agent ---
    sim = simulate_price_change(
        db,
        PriceSimRequest(
            sku=body.sku,
            price_change_pct=body.price_change_pct,
            simulations=body.simulations,
            horizon_days=body.horizon_days,
            seed=body.seed,
        ),
    )
    simulation = PriceSimulationOut(
        sku=sim.sku,
        baseline_price=sim.baseline_price,
        new_price=sim.new_price,
        price_change_pct=sim.price_change_pct,
        elasticity=sim.elasticity,
        simulations=sim.simulations,
        horizon_days=sim.horizon_days,
        starting_inventory=sim.starting_inventory,
        base_weekly_demand=sim.base_weekly_demand,
        expected_revenue=sim.expected_revenue,
        expected_profit=sim.expected_profit,
        revenue_p10=sim.revenue_p10,
        revenue_p90=sim.revenue_p90,
        profit_p10=sim.profit_p10,
        profit_p90=sim.profit_p90,
        stockout_probability=sim.stockout_probability,
        risk_note=sim.risk_note,
    )
    trace.append(
        AgentStep(
            agent="finance",
            role="Simulate financial outcomes under price change",
            summary=(
                f"Expected profit={sim.expected_profit}, p10 profit={sim.profit_p10}, "
                f"stockout_probability={sim.stockout_probability}."
            ),
        )
    )

    # --- Critic agent ---
    risks: list[str] = []
    if sim.stockout_probability >= 0.3:
        risks.append("High simulated stockout probability under this price change.")
    elif sim.stockout_probability >= 0.1:
        risks.append("Moderate stockout risk; inventory coverage may be tight.")
    if sim.expected_profit < 0:
        risks.append("Expected profit is negative in the simulation.")
    if abs(body.price_change_pct) > 15:
        risks.append("Price move exceeds 15%; executive approval may be required by pricing policy.")
    elif abs(body.price_change_pct) > 5:
        risks.append("Price move exceeds 5%; Finance review may be required by pricing policy.")
    if body.sku in twin.low_stock_skus or any(
        body.sku == sku for sku in twin.low_stock_skus
    ):
        risks.append("SKU appears on the digital-twin low-stock list.")
    # Policy keyword hints from research
    joined_policy = " ".join(policy.findings).lower()
    if "14" in joined_policy and body.price_change_pct < 0:
        risks.append(
            "Promotional/discount context may trigger the 14-day coverage approval rule."
        )
    if not risks:
        risks.append("No major red flags from critic checks under current assumptions.")

    trace.append(
        AgentStep(
            agent="critic",
            role="Challenge assumptions and surface risks",
            summary="; ".join(risks),
        )
    )

    # --- Manager recommendation ---
    hard_block = sim.stockout_probability >= 0.5 or (
        sim.expected_profit < 0 and sim.profit_p90 < 0
    )
    needs_human = abs(body.price_change_pct) > 5 or sim.stockout_probability >= 0.2
    approve = (not hard_block) and sim.expected_profit >= 0 and sim.stockout_probability < 0.35

    if hard_block:
        recommendation = (
            f"Reject automated approval for {body.sku} at {body.price_change_pct}%: "
            "simulation shows unacceptable downside under current assumptions."
        )
    elif approve and not needs_human:
        recommendation = (
            f"Conditionally support {body.price_change_pct}% change on {body.sku}: "
            "expected profit is non-negative and stockout risk looks manageable."
        )
    elif approve:
        recommendation = (
            f"Possible upside for {body.sku} at {body.price_change_pct}%, but route to "
            "human approval because policy thresholds or moderate risk apply."
        )
    else:
        recommendation = (
            f"Do not auto-approve {body.sku} at {body.price_change_pct}% without changes: "
            "review inventory, margin, or a milder price move first."
        )

    next_actions = [
        "Confirm live inventory coverage days for the SKU",
        "Attach simulation p10/p90 to the approval packet",
        "If discounting, verify 14-day coverage / manager approval rules",
    ]
    if needs_human:
        next_actions.insert(0, "Request human approval before executing the price change")

    trace.append(
        AgentStep(
            agent="manager",
            role="Combine evidence into a recommendation",
            summary=recommendation,
        )
    )

    return PriceDecisionOut(
        decision_id=decision_id,
        question=question,
        plan=plan,
        agent_trace=trace,
        digital_twin=twin,
        policy=policy,
        simulation=simulation,
        recommendation=recommendation,
        approve=approve and not hard_block,
        risks=risks,
        next_actions=next_actions,
    )
