"""Add RLS policies and token revocation table.

Revision ID: 20240909130000
Revises: 20240904115900_initial_schema
Create Date: 2024-09-09 13:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20240909130000"
down_revision: Union[str, None] = "20240904115900_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PG_ROLE = "motogestor_app"


def upgrade() -> None:
    op.create_table(
        "revoked_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jti", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_type", sa.String(length=20), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("reason", sa.String(length=255), nullable=True),
    )

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

    tenant_guard = "COALESCE(current_setting('app.current_tenant', true), '-1')::int"

    op.execute("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenants FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY tenants_isolation ON tenants
        USING (id = {tenant_guard})
        WITH CHECK (id = {tenant_guard});
        """
    )

    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY users_isolation ON users
        USING (tenant_id = {tenant_guard})
        WITH CHECK (tenant_id = {tenant_guard});
        """
    )

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON tenants, users TO motogestor_app")


def downgrade() -> None:
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenants DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS users_isolation ON users")
    op.execute("DROP POLICY IF EXISTS tenants_isolation ON tenants")
    op.execute("REVOKE ALL PRIVILEGES ON tenants, users FROM motogestor_app")
    op.drop_table("revoked_tokens")
