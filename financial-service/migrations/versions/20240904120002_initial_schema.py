"""Initial schema for financial-service

Revision ID: 20240904120002
Revises: 
Create Date: 2024-09-04 00:00:02.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20240904120002"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "accounts_receivable",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("customer_name", sa.String(length=120), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("received_amount", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("received_at", sa.DateTime(), nullable=True),
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_accounts_receivable_tenant_id",
        "accounts_receivable",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "accounts_payable",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("supplier_name", sa.String(length=120), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("paid_amount", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_accounts_payable_tenant_id", "accounts_payable", ["tenant_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_accounts_payable_tenant_id", table_name="accounts_payable")
    op.drop_table("accounts_payable")
    op.drop_index("ix_accounts_receivable_tenant_id", table_name="accounts_receivable")
    op.drop_table("accounts_receivable")
