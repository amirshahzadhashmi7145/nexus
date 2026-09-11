from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field

Money = Annotated[Decimal, Field(max_digits=14, decimal_places=2, examples=["79.00"])]


class PriceSimulationIn(BaseModel):
    sku: str = Field(examples=["P-0001"])
    price_change_pct: float = Field(
        description="Percent change, e.g. -10 for a 10% discount",
        examples=[-10.0],
    )
    simulations: int = Field(default=200, ge=10, le=5000, examples=[200])
    horizon_days: int = Field(default=30, ge=1, le=365, examples=[30])
    elasticity: float = Field(
        default=-1.2,
        description="Demand elasticity (negative => higher price lowers demand)",
        examples=[-1.2],
    )
    seed: int = Field(default=42, examples=[42])


class PriceSimulationOut(BaseModel):
    sku: str
    baseline_price: Money
    new_price: Money
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
