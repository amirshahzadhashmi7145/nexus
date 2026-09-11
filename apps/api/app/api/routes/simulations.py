from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas_simulation import PriceSimulationIn, PriceSimulationOut
from app.services.simulation import PriceSimRequest, simulate_price_change

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.post("/price-change", response_model=PriceSimulationOut)
def post_price_change_simulation(
    body: PriceSimulationIn,
    db: Session = Depends(get_db),
) -> PriceSimulationOut:
    try:
        result = simulate_price_change(
            db,
            PriceSimRequest(
                sku=body.sku,
                price_change_pct=body.price_change_pct,
                simulations=body.simulations,
                horizon_days=body.horizon_days,
                elasticity=body.elasticity,
                seed=body.seed,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return PriceSimulationOut(
        sku=result.sku,
        baseline_price=result.baseline_price,
        new_price=result.new_price,
        price_change_pct=result.price_change_pct,
        elasticity=result.elasticity,
        simulations=result.simulations,
        horizon_days=result.horizon_days,
        starting_inventory=result.starting_inventory,
        base_weekly_demand=result.base_weekly_demand,
        expected_revenue=result.expected_revenue,
        expected_profit=result.expected_profit,
        revenue_p10=result.revenue_p10,
        revenue_p90=result.revenue_p90,
        profit_p10=result.profit_p10,
        profit_p90=result.profit_p90,
        stockout_probability=result.stockout_probability,
        risk_note=result.risk_note,
    )
