from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas import OrderItemOut, OrderListOut, OrderOut
from app.services import catalog

router = APIRouter(prefix="/orders", tags=["orders"])


def _to_order_out(order) -> OrderOut:
    items = [
        OrderItemOut(
            id=item.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            line_total=item.line_total,
            sku=item.product.sku if item.product else None,
        )
        for item in order.items
    ]
    return OrderOut(
        id=order.id,
        external_id=order.external_id,
        customer_id=order.customer_id,
        status=order.status,
        ordered_at=order.ordered_at,
        total_amount=order.total_amount,
        items=items,
    )


@router.get("", response_model=OrderListOut)
def get_orders(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> OrderListOut:
    rows = catalog.list_orders(db, limit=limit, offset=offset)
    items = [_to_order_out(row) for row in rows]
    return OrderListOut(items=items, count=len(items))


@router.get("/{external_id}", response_model=OrderOut)
def get_order(external_id: str, db: Session = Depends(get_db)) -> OrderOut:
    order = catalog.get_order_by_external_id(db, external_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Order not found: {external_id}")
    return _to_order_out(order)
