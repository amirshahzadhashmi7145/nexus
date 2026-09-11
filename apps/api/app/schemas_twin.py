from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class SegmentCount(BaseModel):
    segment: str
    customers: int


class SupplierReliabilityCount(BaseModel):
    reliability: str
    suppliers: int


class DigitalTwinOut(BaseModel):
    """Snapshot of NovaCart derived from source tables (not a separate store)."""

    organization: str = "NovaCart"
    as_of: datetime
    revenue: Decimal
    cogs: Decimal
    profit: Decimal
    inventory_units: int
    inventory_value: Decimal
    order_count: int
    average_order_value: Decimal
    customer_count: int
    product_count: int
    supplier_count: int
    warehouse_count: int
    customers_by_segment: list[SegmentCount] = Field(default_factory=list)
    suppliers_by_reliability: list[SupplierReliabilityCount] = Field(default_factory=list)
    low_stock_skus: list[str] = Field(default_factory=list)
