"""NovaCart synthetic data generation.

Learn: a seed makes 'random' reproducible. Same seed + same counts = same company.
We insert parents before children so foreign keys never point at missing rows.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from random import Random

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

SEGMENTS = ["frequent", "occasional", "high_value", "discount_sensitive", "inactive"]
RELIABILITY = ["reliable", "average", "unreliable"]
DEMAND_TIERS = ["high", "normal", "slow"]  # ~10% / 60% / 30% via weights
CATEGORIES = ["electronics", "home", "apparel", "grocery", "accessories"]
REGIONS = ["EU", "US", "APAC"]


@dataclass(frozen=True)
class GenerateConfig:
    seed: int = 42
    customers: int = 100
    products: int = 50
    orders: int = 500
    suppliers: int = 8
    warehouses: int = 3
    history_days: int = 180


@dataclass
class GenerateResult:
    suppliers: int
    warehouses: int
    customers: int
    products: int
    inventory_rows: int
    orders: int
    order_items: int
    financial_records: int


def _money(value: float) -> Decimal:
    return Decimal(str(round(value, 2)))


def generate_novacart(session: Session, config: GenerateConfig | None = None) -> GenerateResult:
    cfg = config or GenerateConfig()
    rng = Random(cfg.seed)
    start = datetime(2025, 9, 1, tzinfo=UTC)

    suppliers: list[Supplier] = []
    for i in range(cfg.suppliers):
        reliability = RELIABILITY[i % len(RELIABILITY)]
        lead = {"reliable": 3, "average": 7, "unreliable": 14}[reliability]
        suppliers.append(
            Supplier(
                external_id=f"SUP-{i + 1:03d}",
                name=f"Supplier {i + 1}",
                reliability=reliability,
                lead_time_days=lead,
            )
        )
    session.add_all(suppliers)
    session.flush()

    warehouses: list[Warehouse] = []
    for i in range(cfg.warehouses):
        warehouses.append(
            Warehouse(
                external_id=f"WH-{i + 1:03d}",
                name=f"Warehouse {i + 1}",
                region=REGIONS[i % len(REGIONS)],
            )
        )
    session.add_all(warehouses)
    session.flush()

    customers: list[Customer] = []
    for i in range(cfg.customers):
        customers.append(
            Customer(
                external_id=f"CUS-{i + 1:05d}",
                name=f"Customer {i + 1}",
                email=f"customer{i + 1}@novacart.test",
                segment=rng.choice(SEGMENTS),
                created_at=start - timedelta(days=rng.randint(0, cfg.history_days)),
            )
        )
    session.add_all(customers)
    session.flush()

    products: list[Product] = []
    for i in range(cfg.products):
        demand_tier = rng.choices(DEMAND_TIERS, weights=[10, 60, 30], k=1)[0]
        cost = rng.uniform(2.0, 80.0)
        margin = {"high": 1.8, "normal": 1.5, "slow": 1.25}[demand_tier]
        products.append(
            Product(
                sku=f"P-{i + 1:04d}",
                name=f"Product {i + 1}",
                category=rng.choice(CATEGORIES),
                unit_cost=_money(cost),
                unit_price=_money(cost * margin),
                demand_tier=demand_tier,
                supplier_id=rng.choice(suppliers).id,
            )
        )
    session.add_all(products)
    session.flush()

    inventory_rows: list[Inventory] = []
    for product in products:
        for warehouse in warehouses:
            base = {"high": 200, "normal": 80, "slow": 25}[product.demand_tier]
            qty = max(0, int(rng.gauss(base, base * 0.25)))
            inventory_rows.append(
                Inventory(
                    product_id=product.id,
                    warehouse_id=warehouse.id,
                    quantity_on_hand=qty,
                    reorder_point=max(5, qty // 5),
                )
            )
    session.add_all(inventory_rows)
    session.flush()

    # Popular products get picked more often (weighted by demand tier).
    product_weights = [
        {"high": 5.0, "normal": 2.0, "slow": 0.5}[p.demand_tier] for p in products
    ]

    orders: list[Order] = []
    order_items: list[OrderItem] = []
    financial_records: list[FinancialRecord] = []

    for i in range(cfg.orders):
        customer = rng.choice(customers)
        ordered_at = start + timedelta(
            days=rng.randint(0, cfg.history_days),
            hours=rng.randint(0, 23),
            minutes=rng.randint(0, 59),
        )
        order = Order(
            external_id=f"ORD-{i + 1:06d}",
            customer_id=customer.id,
            status="completed",
            ordered_at=ordered_at.replace(tzinfo=None),
            total_amount=Decimal("0.00"),
        )
        session.add(order)
        session.flush()

        total = Decimal("0.00")
        for _ in range(rng.randint(1, 4)):
            product = rng.choices(products, weights=product_weights, k=1)[0]
            qty = rng.randint(1, 5)
            line = _money(float(product.unit_price) * qty)
            total += line
            order_items.append(
                OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=qty,
                    unit_price=product.unit_price,
                    line_total=line,
                )
            )

        order.total_amount = total
        financial_records.append(
            FinancialRecord(
                record_date=ordered_at.date(),
                category="revenue",
                description=f"Revenue for {order.external_id}",
                amount=total,
                order_id=order.id,
            )
        )
        orders.append(order)

    session.add_all(order_items)
    session.add_all(financial_records)
    session.commit()

    return GenerateResult(
        suppliers=len(suppliers),
        warehouses=len(warehouses),
        customers=len(customers),
        products=len(products),
        inventory_rows=len(inventory_rows),
        orders=len(orders),
        order_items=len(order_items),
        financial_records=len(financial_records),
    )
