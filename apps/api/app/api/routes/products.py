from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas import ProductListOut, ProductOut
from app.services import catalog

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductListOut)
def get_products(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> ProductListOut:
    rows = catalog.list_products(db, limit=limit, offset=offset)
    items = [ProductOut.model_validate(row) for row in rows]
    return ProductListOut(items=items, count=len(items))


@router.get("/{sku}", response_model=ProductOut)
def get_product(sku: str, db: Session = Depends(get_db)) -> ProductOut:
    product = catalog.get_product_by_sku(db, sku)
    if product is None:
        raise HTTPException(status_code=404, detail=f"Product not found: {sku}")
    return ProductOut.model_validate(product)
