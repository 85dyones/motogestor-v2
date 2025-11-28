from __future__ import annotations

from app.models import Tenant, User, db
from faker import Faker
from werkzeug.security import generate_password_hash

fake = Faker()


def create_tenant(name: str | None = None, plan: str = "BASIC") -> Tenant:
    tenant = Tenant(name=name or fake.company(), plan=plan)
    db.session.add(tenant)
    db.session.flush()
    return tenant


def create_user(tenant: Tenant, password: str = "secret123", **overrides) -> User:
    user = User(
        name=overrides.get("name", fake.name()),
        email=overrides.get("email", fake.unique.email()),
        password_hash=generate_password_hash(password),
        tenant_id=tenant.id,
        role=overrides.get("role", "OWNER"),
        plan=overrides.get("plan", tenant.plan),
    )
    db.session.add(user)
    db.session.commit()
    return user
