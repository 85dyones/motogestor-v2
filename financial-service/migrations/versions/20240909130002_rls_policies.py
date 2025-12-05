"""Add per-tenant RLS for financial tables.

Revision ID: 20240909130002
Revises: 20240904120002
Create Date: 2024-09-09 13:10:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20240909130002"
down_revision: Union[str, None] = "20240904120002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PG_ROLE = "motogestor_app"
TENANT_EXPR = "COALESCE(current_setting('app.current_tenant', true), '-1')::int"
TABLES = ["accounts_receivable", "accounts_payable"]


def upgrade() -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{PG_ROLE}') THEN
                CREATE ROLE {PG_ROLE};
            END IF;
        END $$;
        """
    )

    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY {table}_tenant_isolation ON {table}
            USING (tenant_id = {TENANT_EXPR})
            WITH CHECK (tenant_id = {TENANT_EXPR});
            """
        )

    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON "
        + ",".join(TABLES)
        + " TO motogestor_app"
    )


def downgrade() -> None:
    op.execute(
        "REVOKE ALL PRIVILEGES ON " + ",".join(TABLES) + " FROM motogestor_app"
    )
    for table in TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
