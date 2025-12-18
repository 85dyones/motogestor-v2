"""Initial schema for management-service

Revision ID: 20240904120001
Revises: 
Create Date: 2024-09-04 00:00:01.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20240904120001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=120), nullable=True),
        sa.Column("document", sa.String(length=30), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_customers_tenant_id", "customers", ["tenant_id"], unique=False)

    op.create_table(
        "parts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("sku", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "quantity_in_stock",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("min_stock", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_parts_tenant_id", "parts", ["tenant_id"], unique=False)

    op.create_table(
        "motorcycles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("brand", sa.String(length=80), nullable=True),
        sa.Column("model", sa.String(length=80), nullable=True),
        sa.Column("plate", sa.String(length=10), nullable=True),
        sa.Column("year", sa.String(length=4), nullable=True),
        sa.Column("vin", sa.String(length=20), nullable=True),
        sa.Column("km_current", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_motorcycles_plate", "motorcycles", ["plate"], unique=False)
    op.create_index("ix_motorcycles_tenant_id", "motorcycles", ["tenant_id"], unique=False)

    op.create_table(
        "service_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("motorcycle_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="OPEN"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")
        ),
        sa.Column("scheduled_date", sa.DateTime(), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("total_parts", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("total_labor", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["motorcycle_id"], ["motorcycles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_service_orders_tenant_id", "service_orders", ["tenant_id"], unique=False)

    op.create_table(
        "service_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("service_order_id", sa.Integer(), nullable=False),
        sa.Column("item_type", sa.String(length=10), nullable=False),
        sa.Column("part_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("quantity", sa.Numeric(10, 2), nullable=False, server_default=sa.text("1")),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("total", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["part_id"], ["parts.id"]),
        sa.ForeignKeyConstraint(["service_order_id"], ["service_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_service_items_tenant_id", "service_items", ["tenant_id"], unique=False)

    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("part_id", sa.Integer(), nullable=False),
        sa.Column("movement_type", sa.String(length=10), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("related_order_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(["part_id"], ["parts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stock_movements_tenant_id", "stock_movements", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_stock_movements_tenant_id", table_name="stock_movements")
    op.drop_table("stock_movements")
    op.drop_index("ix_service_items_tenant_id", table_name="service_items")
    op.drop_table("service_items")
    op.drop_index("ix_service_orders_tenant_id", table_name="service_orders")
    op.drop_table("service_orders")
    op.drop_index("ix_motorcycles_tenant_id", table_name="motorcycles")
    op.drop_index("ix_motorcycles_plate", table_name="motorcycles")
    op.drop_table("motorcycles")
    op.drop_index("ix_parts_tenant_id", table_name="parts")
    op.drop_table("parts")
    op.drop_index("ix_customers_tenant_id", table_name="customers")
    op.drop_table("customers")
