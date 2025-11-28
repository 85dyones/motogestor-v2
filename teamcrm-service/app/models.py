# teamcrm-service/app/models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Staff(db.Model):
    __tablename__ = "staff"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False, index=True)

    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50))  # mechanic, attendant, admin, etc.
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))

    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False, index=True)

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)

    status = db.Column(
        db.String(20), default="OPEN"
    )  # OPEN | IN_PROGRESS | WAITING | DONE | CANCELLED
    priority = db.Column(
        db.String(20), default="NORMAL"
    )  # LOW | NORMAL | HIGH | URGENT

    assigned_to_id = db.Column(db.Integer, db.ForeignKey("staff.id"))
    related_order_id = db.Column(db.Integer)  # id da OS no management-service
    customer_id = db.Column(db.Integer)  # id do cliente no management-service

    due_date = db.Column(db.Date)
    completed_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    assigned_to = db.relationship("Staff", backref="tasks")


class Interaction(db.Model):
    __tablename__ = "interactions"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False, index=True)

    customer_id = db.Column(db.Integer)  # id no management-service
    related_order_id = db.Column(db.Integer)  # opcional, se interação for sobre uma OS

    channel = db.Column(db.String(20))  # WHATSAPP | PHONE | IN_PERSON | EMAIL | OTHER
    direction = db.Column(
        db.String(10)
    )  # IN | OUT (cliente → oficina / oficina → cliente)
    summary = db.Column(db.String(255))
    details = db.Column(db.Text)

    staff_id = db.Column(db.Integer, db.ForeignKey("staff.id"))

    occurred_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    staff = db.relationship("Staff", backref="interactions")
