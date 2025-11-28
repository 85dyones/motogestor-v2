# financial-service/app/models.py
from datetime import date, datetime
from decimal import Decimal

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class AccountReceivable(db.Model):
    __tablename__ = "accounts_receivable"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False, index=True)

    source_type = db.Column(db.String(20))  # OS | MANUAL
    source_id = db.Column(db.Integer)  # service_order_id ou outro id externo

    customer_name = db.Column(db.String(120))
    description = db.Column(db.String(255))

    issue_date = db.Column(db.Date, default=date.today)
    due_date = db.Column(db.Date)

    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(
        db.String(20), default="PENDING"
    )  # PENDING | PARTIAL | PAID | CANCELLED

    received_amount = db.Column(db.Numeric(10, 2), default=0)
    received_at = db.Column(db.DateTime)
    payment_method = db.Column(db.String(50))  # PIX, DINHEIRO, CARTAO, BOLETO etc.
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class AccountPayable(db.Model):
    __tablename__ = "accounts_payable"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False, index=True)

    supplier_name = db.Column(db.String(120))
    description = db.Column(db.String(255))
    category = db.Column(db.String(50))  # PARTS, RENT, UTILITIES, PAYROLL, TAXES, OTHER

    issue_date = db.Column(db.Date, default=date.today)
    due_date = db.Column(db.Date)

    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(
        db.String(20), default="PENDING"
    )  # PENDING | PARTIAL | PAID | CANCELLED

    paid_amount = db.Column(db.Numeric(10, 2), default=0)
    paid_at = db.Column(db.DateTime)
    payment_method = db.Column(db.String(50))
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


def _to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
