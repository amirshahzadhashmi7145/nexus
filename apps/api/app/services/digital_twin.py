"""Digital twin = derived metrics from source-of-truth tables.

Learn:
- We do NOT store a second copy of the company.
- We compute a snapshot from orders/inventory/customers so it's reproducible.
- Simulation (Phase 4) will start from this kind of state.
"""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Customer, Inventory, Order, OrderItem, Product, Supplier, Warehouse
from app.schemas_twin import DigitalTwinOut, SegmentCount, SupplierReliabilityCount


def build_digital_twin(db: Session) -> DigitalTwinOut:
    revenue = db.scalar(select(func.coalesce(func.sum(Order.total_amount), 0))) or Decimal("0")
    order_count = db.scalar(select(func.count()).select_from(Order)) or 0

    # COGS ≈ sum(order_item.qty * product.unit_cost)
    cogs_rows = db.execute(
        select(OrderItem.quantity, Product.unit_cost).join(Product, OrderItem.product_id == Product.id)
    ).all()
    cogs = sum((Decimal(qty) * cost for qty, cost in cogs_rows), Decimal("0.00"))
    profit = Decimal(revenue) - cogs

    inv_rows = db.scalars(
        select(Inventory).options(selectinload(Inventory.product))
    ).all()
    inventory_units = sum(row.quantity_on_hand for row in inv_rows)
    inventory_value = sum(
        (Decimal(row.quantity_on_hand) * row.product.unit_cost for row in inv_rows if row.product),
        Decimal("0.00"),
    )
    low_stock = sorted(
        {
            row.product.sku
            for row in inv_rows
            if row.product and row.quantity_on_hand <= row.reorder_point
        }
    )

    customer_count = db.scalar(select(func.count()).select_from(Customer)) or 0
    product_count = db.scalar(select(func.count()).select_from(Product)) or 0
    supplier_count = db.scalar(select(func.count()).select_from(Supplier)) or 0
    warehouse_count = db.scalar(select(func.count()).select_from(Warehouse)) or 0

    segment_rows = db.execute(
        select(Customer.segment, func.count()).group_by(Customer.segment).order_by(Customer.segment)
    ).all()
    reliability_rows = db.execute(
        select(Supplier.reliability, func.count())
        .group_by(Supplier.reliability)
        .order_by(Supplier.reliability)
    ).all()

    aov = (Decimal(revenue) / order_count) if order_count else Decimal("0.00")

    return DigitalTwinOut(
        as_of=datetime.now(UTC),
        revenue=Decimal(revenue).quantize(Decimal("0.01")),
        cogs=cogs.quantize(Decimal("0.01")),
        profit=profit.quantize(Decimal("0.01")),
        inventory_units=inventory_units,
        inventory_value=inventory_value.quantize(Decimal("0.01")),
        order_count=order_count,
        average_order_value=aov.quantize(Decimal("0.01")),
        customer_count=customer_count,
        product_count=product_count,
        supplier_count=supplier_count,
        warehouse_count=warehouse_count,
        customers_by_segment=[
            SegmentCount(segment=segment, customers=count) for segment, count in segment_rows
        ],
        suppliers_by_reliability=[
            SupplierReliabilityCount(reliability=rel, suppliers=count)
            for rel, count in reliability_rows
        ],
        low_stock_skus=low_stock[:20],
    )
