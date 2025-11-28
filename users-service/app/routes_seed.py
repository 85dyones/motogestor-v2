from flask import Blueprint, jsonify
from werkzeug.security import generate_password_hash

from .models import Tenant, User, db

bp = Blueprint("seed_routes", __name__)


@bp.route("/seed-demo", methods=["POST"])
def seed_demo_user():
    """
    Cria um tenant + usuário demo, se ainda não existirem.

    - email: demo@motogestor.com
    - senha: demo123
    """
    email = "demo@motogestor.com"
    password = "demo123"

    tenant = Tenant.query.filter_by(name="Oficina Demo").first()
    if not tenant:
        tenant = Tenant(name="Oficina Demo", plan="BASIC")
        db.session.add(tenant)
        db.session.flush()

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(
            name="Usuário Demo",
            email=email,
            password_hash=generate_password_hash(password),
            tenant_id=tenant.id,
            role="OWNER",
            plan="BASIC",
        )
        db.session.add(user)

    db.session.commit()

    return (
        jsonify(
            {
                "message": "Usuário demo garantido com sucesso.",
                "tenant": {
                    "id": tenant.id,
                    "name": tenant.name,
                    "plan": tenant.plan,
                },
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "tenant_id": user.tenant_id,
                },
                "credentials": {
                    "email": email,
                    "password": password,
                },
            }
        ),
        201,
    )
