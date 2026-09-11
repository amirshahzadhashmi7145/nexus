"""Data quality checks for NovaCart.

Learn: generation without validation is hope. These rules catch broken twins early.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Customer,
    FinancialRecord,
    Inventory,
    Order,
    OrderItem,
    Product,
    Supplier,
    Warehouse,
)


@dataclass
class ValidationIssue:
    code: str
    message: str


def validate_novacart(session: Session) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    orphan_orders = session.scalar(
        select(func.count())
        .select_from(Order)
        .outerjoin(Customer, Order.customer_id == Customer.id)
        .where(Customer.id.is_(None))
    )
    if orphan_orders:
        issues.append(
            ValidationIssue("orphan_order_customer", f"{orphan_orders} orders missing customer")
        )

    orphan_items = session.scalar(
        select(func.count())
        .select_from(OrderItem)
        .outerjoin(Product, OrderItem.product_id == Product.id)
        .where(Product.id.is_(None))
    )
    if orphan_items:
        issues.append(
            ValidationIssue("orphan_order_item_product", f"{orphan_items} items missing product")
        )

    bad_qty = session.scalar(select(func.count()).select_from(OrderItem).where(OrderItem.quantity <= 0))
    if bad_qty:
        issues.append(ValidationIssue("non_positive_quantity", f"{bad_qty} items with quantity <= 0"))

    bad_price = session.scalar(
        select(func.count()).select_from(Product).where(Product.unit_price < 0)
    )
    if bad_price:
        issues.append(ValidationIssue("negative_price", f"{bad_price} products with negative price"))

    bad_stock = session.scalar(
        select(func.count()).select_from(Inventory).where(Inventory.quantity_on_hand < 0)
    )
    if bad_stock:
        issues.append(ValidationIssue("negative_stock", f"{bad_stock} inventory rows with negative stock"))

    # Revenue financial rows should match order totals when linked.
    mismatches = session.execute(
        select(Order.external_id, Order.total_amount, FinancialRecord.amount)
        .join(FinancialRecord, FinancialRecord.order_id == Order.id)
        .where(FinancialRecord.category == "revenue")
        .where(FinancialRecord.amount != Order.total_amount)
    ).all()
    if mismatches:
        issues.append(
            ValidationIssue(
                "revenue_mismatch",
                f"{len(mismatches)} revenue records do not match order totals",
            )
        )

    # Sanity: core tables not empty after a generate run.
    for model, label in (
        (Supplier, "suppliers"),
        (Warehouse, "warehouses"),
        (Customer, "customers"),
        (Product, "products"),
        (Inventory, "inventory"),
        (Order, "orders"),
        (OrderItem, "order_items"),
        (FinancialRecord, "financial_records"),
    ):
        count = session.scalar(select(func.count()).select_from(model)) or 0
        if count == 0:
            issues.append(ValidationIssue("empty_table", f"{label} table is empty"))

    return issues
