from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.data import GenerateConfig, generate_novacart, validate_novacart
from app.db.base import Base
from app.db.session import make_engine
from app.models import Customer, Order, OrderItem, Product


def _fresh_session() -> Session:
    engine = make_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_generator_is_deterministic() -> None:
    cfg = GenerateConfig(seed=42, customers=20, products=10, orders=30, suppliers=3, warehouses=2)

    s1 = _fresh_session()
    r1 = generate_novacart(s1, cfg)
    skus_1 = sorted(s1.scalars(select(Product.sku)).all())
    emails_1 = sorted(s1.scalars(select(Customer.email)).all())
    totals_1 = sorted(s1.scalars(select(Order.total_amount)).all())
    s1.close()

    s2 = _fresh_session()
    r2 = generate_novacart(s2, cfg)
    skus_2 = sorted(s2.scalars(select(Product.sku)).all())
    emails_2 = sorted(s2.scalars(select(Customer.email)).all())
    totals_2 = sorted(s2.scalars(select(Order.total_amount)).all())
    s2.close()

    assert r1 == r2
    assert skus_1 == skus_2
    assert emails_1 == emails_2
    assert totals_1 == totals_2


def test_generator_passes_validation() -> None:
    session = _fresh_session()
    generate_novacart(
        session,
        GenerateConfig(seed=7, customers=25, products=12, orders=40, suppliers=4, warehouses=2),
    )
    assert validate_novacart(session) == []


def test_order_items_have_positive_qty_and_matching_line_totals() -> None:
    session = _fresh_session()
    generate_novacart(
        session,
        GenerateConfig(seed=1, customers=15, products=8, orders=25, suppliers=3, warehouses=2),
    )
    items = session.scalars(select(OrderItem)).all()
    assert items
    for item in items:
        assert item.quantity > 0
        assert item.unit_price >= 0
        assert item.line_total == (item.unit_price * item.quantity).quantize(Decimal("0.01"))

    # Every order has at least one item
    order_count = session.scalar(select(func.count()).select_from(Order)) or 0
    distinct_orders = session.scalar(select(func.count(func.distinct(OrderItem.order_id)))) or 0
    assert order_count == distinct_orders
