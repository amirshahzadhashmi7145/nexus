from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas import InventoryListOut, InventoryOut
from app.services import catalog

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=InventoryListOut)
def get_inventory(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> InventoryListOut:
    rows = catalog.list_inventory(db, limit=limit, offset=offset)
    items = [
        InventoryOut(
            id=row.id,
            product_id=row.product_id,
            warehouse_id=row.warehouse_id,
            quantity_on_hand=row.quantity_on_hand,
            reorder_point=row.reorder_point,
            sku=row.product.sku if row.product else None,
            warehouse_external_id=row.warehouse.external_id if row.warehouse else None,
        )
        for row in rows
    ]
    return InventoryListOut(items=items, count=len(items))
