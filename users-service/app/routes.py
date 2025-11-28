from flask import Blueprint, jsonify, request
from .models import db, User, Tenant

bp = Blueprint("users", __name__)


@bp.get("/")
def list_users():
    users = User.query.all()
    return jsonify(
        [
            {"id": u.id, "name": u.name, "email": u.email, "tenant_id": u.tenant_id}
            for u in users
        ]
    )


@bp.post("/seed-demo")
def seed_demo():
    """Cria um tenant + user demo só pra testar banco."""
    tenant = Tenant(name="Oficina Demo", slug="oficina-demo", plan="basic")
    db.session.add(tenant)
    db.session.flush()

    user = User(tenant_id=tenant.id, name="Usuário Demo", email="demo@motogestor.com")
    db.session.add(user)
    db.session.commit()

    return jsonify(
        {"message": "Demo seeded", "tenant_id": tenant.id, "user_id": user.id}
    )


@bp.post("/login")
def login():
    data = request.get_json() or {}
    email = data.get("email")
    if not email:
        return jsonify({"error": "email é obrigatório"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "usuário não encontrado"}), 404

    # aqui depois entra JWT de verdade
    return jsonify(
        {
            "message": "login ok (placeholder)",
            "email": email,
            "tenant_id": user.tenant_id,
        }
    )
