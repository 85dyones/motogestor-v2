# management-service/app/models.py
from datetime import datetime
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    document = db.Column(db.String(30))  # CPF/CNPJ
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Motorcycle(db.Model):
    __tablename__ = "motorcycles"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    brand = db.Column(db.String(80))
    model = db.Column(db.String(80))
    plate = db.Column(db.String(10), index=True)
    year = db.Column(db.String(4))
    vin = db.Column(db.String(20))
    km_current = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    customer = db.relationship("Customer", backref="motorcycles")


class Part(db.Model):
    __tablename__ = "parts"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False, index=True)
    sku = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), default=0)
    quantity_in_stock = db.Column(db.Integer, default=0)
    min_stock = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class ServiceOrder(db.Model):
    __tablename__ = "service_orders"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    motorcycle_id = db.Column(
        db.Integer, db.ForeignKey("motorcycles.id"), nullable=False
    )
    status = db.Column(
        db.String(20), default="OPEN"
    )  # OPEN, IN_PROGRESS, WAITING_PARTS, COMPLETED, CANCELLED
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_date = db.Column(db.DateTime)
    closed_at = db.Column(db.DateTime)

    total_parts = db.Column(db.Numeric(10, 2), default=0)
    total_labor = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(10, 2), default=0)

    customer = db.relationship("Customer")
    motorcycle = db.relationship("Motorcycle")


class ServiceItem(db.Model):
    __tablename__ = "service_items"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False, index=True)
    service_order_id = db.Column(
        db.Integer, db.ForeignKey("service_orders.id"), nullable=False
    )
    item_type = db.Column(db.String(10), nullable=False)  # part | labor
    part_id = db.Column(db.Integer, db.ForeignKey("parts.id"))
    description = db.Column(db.String(255))
    quantity = db.Column(db.Numeric(10, 2), default=1)
    unit_price = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), default=0)

    order = db.relationship("ServiceOrder", backref="items")
    part = db.relationship("Part")


class StockMovement(db.Model):
    __tablename__ = "stock_movements"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False, index=True)
    part_id = db.Column(db.Integer, db.ForeignKey("parts.id"), nullable=False)
    movement_type = db.Column(db.String(10), nullable=False)  # in | out | adjust
    quantity = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255))
    related_order_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    part = db.relationship("Part", backref="movements")


def recalc_order_totals(order: ServiceOrder):
    """Recalculate numeric totals for a ServiceOrder from its items."""
    tp = Decimal("0")
    tl = Decimal("0")
    for i in getattr(order, "items", []):
        val = i.total or Decimal("0")
        if getattr(i, "item_type", "") == "part":
            tp += val
        else:
            tl += val
    order.total_parts = tp
    order.total_labor = tl
    order.total_amount = tp + tl
