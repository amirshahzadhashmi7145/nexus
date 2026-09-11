from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field

# Constrain money so OpenAPI does not invent insane Decimal "examples".
Money = Annotated[
    Decimal,
    Field(max_digits=14, decimal_places=2, examples=["12500.50"]),
]


class SegmentCount(BaseModel):
    segment: str = Field(examples=["high_value"])
    customers: int = Field(examples=[12])


class SupplierReliabilityCount(BaseModel):
    reliability: str = Field(examples=["reliable"])
    suppliers: int = Field(examples=[3])


class DigitalTwinOut(BaseModel):
    """Snapshot of NovaCart derived from source tables (not a separate store)."""

    organization: str = Field(default="NovaCart", examples=["NovaCart"])
    as_of: datetime
    revenue: Money
    cogs: Money
    profit: Money
    inventory_units: int = Field(examples=[1500])
    inventory_value: Money
    order_count: int = Field(examples=[500])
    average_order_value: Money
    customer_count: int = Field(examples=[100])
    product_count: int = Field(examples=[50])
    supplier_count: int = Field(examples=[8])
    warehouse_count: int = Field(examples=[3])
    customers_by_segment: list[SegmentCount] = Field(default_factory=list)
    suppliers_by_reliability: list[SupplierReliabilityCount] = Field(default_factory=list)
    low_stock_skus: list[str] = Field(default_factory=list, examples=[["P-0003", "P-0012"]])
