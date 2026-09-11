"""Price-change Monte Carlo simulation (CPU, no LLM).

Mentor model (transparent, not perfect economics):

  new_price = old_price * (1 + price_change_pct/100)
  elasticity ≈ how much demand moves when price moves (negative for normal goods)
  demand_multiplier = (1 + price_change_pct/100) ** elasticity
  weekly_demand ~ Normal(base_weekly_demand * multiplier, noise)
  sold = min(demand_over_horizon, starting_inventory)
  revenue = sold * new_price
  cogs = sold * unit_cost
  profit = revenue - cogs
  stockout if demand > inventory

Repeat N times with a seed → distribution of outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from random import Random
from statistics import mean, pstdev

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Inventory, OrderItem, Product


@dataclass(frozen=True)
class PriceSimRequest:
    sku: str
    price_change_pct: float
    simulations: int = 200
    horizon_days: int = 30
    elasticity: float = -1.2
    seed: int = 42


@dataclass
class PriceSimResult:
    sku: str
    baseline_price: Decimal
    new_price: Decimal
    price_change_pct: float
    elasticity: float
    simulations: int
    horizon_days: int
    starting_inventory: int
    base_weekly_demand: float
    expected_revenue: float
    expected_profit: float
    revenue_p10: float
    revenue_p90: float
    profit_p10: float
    profit_p90: float
    stockout_probability: float
    risk_note: str


def _percentile(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = int(round((len(sorted_vals) - 1) * p))
    return sorted_vals[max(0, min(idx, len(sorted_vals) - 1))]


def _base_weekly_demand(db: Session, product_id: int) -> float:
    """Estimate weekly units from historical order items (fallback if thin history)."""
    total_qty = db.scalar(
        select(func.coalesce(func.sum(OrderItem.quantity), 0)).where(
            OrderItem.product_id == product_id
        )
    )
    total_qty = int(total_qty or 0)
    # Seed history spans ~180 days ≈ 26 weeks; use that as denominator when we have sales.
    if total_qty <= 0:
        return 5.0
    return max(1.0, total_qty / 26.0)


def simulate_price_change(db: Session, req: PriceSimRequest) -> PriceSimResult:
    product = db.scalar(select(Product).where(Product.sku == req.sku))
    if product is None:
        raise ValueError(f"Product not found: {req.sku}")

    inventory = int(
        db.scalar(
            select(func.coalesce(func.sum(Inventory.quantity_on_hand), 0)).where(
                Inventory.product_id == product.id
            )
        )
        or 0
    )

    baseline_price = Decimal(product.unit_price)
    unit_cost = float(product.unit_cost)
    new_price = float(baseline_price) * (1.0 + req.price_change_pct / 100.0)
    if new_price < 0:
        raise ValueError("New price would be negative")

    base_weekly = _base_weekly_demand(db, product.id)
    weeks = max(req.horizon_days / 7.0, 1 / 7)
    # Constant elasticity-style demand response.
    demand_multiplier = (1.0 + req.price_change_pct / 100.0) ** req.elasticity
    expected_weekly = max(0.1, base_weekly * demand_multiplier)

    rng = Random(req.seed)
    revenues: list[float] = []
    profits: list[float] = []
    stockouts = 0

    for _ in range(req.simulations):
        # Uncertainty: weekly demand noise + mild cost noise.
        weekly = max(0.0, rng.gauss(expected_weekly, expected_weekly * 0.25))
        demand = weekly * weeks
        sold = min(demand, float(inventory))
        stockout = demand > inventory
        if stockout:
            stockouts += 1

        revenue = sold * new_price
        cogs = sold * unit_cost
        profit = revenue - cogs
        revenues.append(revenue)
        profits.append(profit)

    revenues_sorted = sorted(revenues)
    profits_sorted = sorted(profits)
    stockout_p = stockouts / req.simulations

    if stockout_p >= 0.3:
        risk = "High stockout risk under this price/demand scenario."
    elif stockout_p >= 0.1:
        risk = "Moderate stockout risk; watch inventory coverage."
    elif mean(profits) < 0:
        risk = "Expected profit is negative at the simulated price."
    else:
        risk = "Risk looks manageable under current assumptions."

    return PriceSimResult(
        sku=product.sku,
        baseline_price=baseline_price.quantize(Decimal("0.01")),
        new_price=Decimal(str(round(new_price, 2))),
        price_change_pct=req.price_change_pct,
        elasticity=req.elasticity,
        simulations=req.simulations,
        horizon_days=req.horizon_days,
        starting_inventory=inventory,
        base_weekly_demand=round(base_weekly, 3),
        expected_revenue=round(mean(revenues), 2),
        expected_profit=round(mean(profits), 2),
        revenue_p10=round(_percentile(revenues_sorted, 0.10), 2),
        revenue_p90=round(_percentile(revenues_sorted, 0.90), 2),
        profit_p10=round(_percentile(profits_sorted, 0.10), 2),
        profit_p90=round(_percentile(profits_sorted, 0.90), 2),
        stockout_probability=round(stockout_p, 4),
        risk_note=risk,
    )


def revenue_volatility(values: list[float]) -> float:
    """Helper for tests/learning: population stdev of revenues."""
    if len(values) < 2:
        return 0.0
    return float(pstdev(values))
