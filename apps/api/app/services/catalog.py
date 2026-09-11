"""Read services for catalog/ops data.

Learn: routes handle HTTP; services talk to SQLAlchemy. That split keeps tests and
future agent tools from depending on FastAPI request objects.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Inventory, Order, OrderItem, Product


def list_products(db: Session, *, limit: int = 50, offset: int = 0) -> list[Product]:
    stmt = select(Product).order_by(Product.sku).offset(offset).limit(limit)
    return list(db.scalars(stmt))


def get_product_by_sku(db: Session, sku: str) -> Product | None:
    return db.scalar(select(Product).where(Product.sku == sku))


def list_inventory(db: Session, *, limit: int = 100, offset: int = 0) -> list[Inventory]:
    stmt = (
        select(Inventory)
        .options(selectinload(Inventory.product), selectinload(Inventory.warehouse))
        .order_by(Inventory.id)
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(stmt))


def list_orders(db: Session, *, limit: int = 50, offset: int = 0) -> list[Order]:
    stmt = (
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .order_by(Order.ordered_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(stmt))


def get_order_by_external_id(db: Session, external_id: str) -> Order | None:
    stmt = (
        select(Order)
        .where(Order.external_id == external_id)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
    )
    return db.scalar(stmt)
