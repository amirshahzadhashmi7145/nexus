from decimal import Decimal
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import make_engine
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


@pytest.fixture()
def session() -> Session:
    engine = make_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        yield db


def test_order_item_links_customer_product_and_warehouse(session: Session) -> None:
    supplier = Supplier(external_id="SUP-1", name="Acme Supply", reliability="reliable")
    warehouse = Warehouse(external_id="WH-1", name="Central", region="EU")
    customer = Customer(
        external_id="CUS-1",
        name="Ada Buyer",
        email="ada@example.com",
        segment="high_value",
    )
    product = Product(
        sku="P-172",
        name="Nova Headphones",
        category="electronics",
        unit_cost=Decimal("40.00"),
        unit_price=Decimal("79.00"),
        demand_tier="high",
        supplier=supplier,
    )
    inventory = Inventory(
        product=product,
        warehouse=warehouse,
        quantity_on_hand=100,
        reorder_point=20,
    )
    order = Order(
        external_id="ORD-1",
        customer=customer,
        ordered_at=datetime(2026, 1, 15),
        total_amount=Decimal("158.00"),
    )
    item = OrderItem(
        order=order,
        product=product,
        quantity=2,
        unit_price=Decimal("79.00"),
        line_total=Decimal("158.00"),
    )

    session.add_all([supplier, warehouse, customer, product, inventory, order, item])
    session.commit()

    loaded = session.get(Order, order.id)
    assert loaded is not None
    assert loaded.customer.email == "ada@example.com"
    assert loaded.items[0].product.sku == "P-172"
    assert loaded.items[0].product.supplier.name == "Acme Supply"
    assert loaded.items[0].product.inventory_rows[0].warehouse.region == "EU"


def test_inventory_unique_per_product_warehouse(session: Session) -> None:
    supplier = Supplier(external_id="SUP-2", name="Beta", reliability="average")
    warehouse = Warehouse(external_id="WH-2", name="East", region="US")
    product = Product(
        sku="P-200",
        name="Cable",
        category="accessories",
        unit_cost=Decimal("1.00"),
        unit_price=Decimal("5.00"),
        supplier=supplier,
    )
    session.add_all(
        [
            supplier,
            warehouse,
            product,
            Inventory(product=product, warehouse=warehouse, quantity_on_hand=10),
            Inventory(product=product, warehouse=warehouse, quantity_on_hand=5),
        ]
    )
    with pytest.raises(Exception):
        session.commit()


def test_financial_record_can_reference_order(session: Session) -> None:
    customer = Customer(
        external_id="CUS-3",
        name="Lin",
        email="lin@example.com",
    )
    order = Order(
        external_id="ORD-3",
        customer=customer,
        ordered_at=datetime(2026, 2, 1),
        total_amount=Decimal("20.00"),
    )
    session.add_all([customer, order])
    session.flush()

    record = FinancialRecord(
        record_date=order.ordered_at.date(),
        category="revenue",
        description="order revenue",
        amount=Decimal("20.00"),
        order_id=order.id,
    )
    session.add(record)
    session.commit()

    loaded = session.get(FinancialRecord, record.id)
    assert loaded is not None
    assert loaded.order_id == order.id
