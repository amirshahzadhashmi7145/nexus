from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str
    category: str
    unit_cost: Decimal
    unit_price: Decimal
    demand_tier: str
    supplier_id: int


class InventoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    warehouse_id: int
    quantity_on_hand: int
    reorder_point: int
    sku: str | None = None
    warehouse_external_id: str | None = None


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    sku: str | None = None


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str
    customer_id: int
    status: str
    ordered_at: datetime
    total_amount: Decimal
    items: list[OrderItemOut] = Field(default_factory=list)


class ProductListOut(BaseModel):
    items: list[ProductOut]
    count: int


class InventoryListOut(BaseModel):
    items: list[InventoryOut]
    count: int


class OrderListOut(BaseModel):
    items: list[OrderOut]
    count: int
