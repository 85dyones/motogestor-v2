from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from werkzeug.security import check_password_hash, generate_password_hash

from .models import db, User, Tenant

bp = Blueprint("auth_routes", __name__)


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"msg": "Email e senha são obrigatórios."}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"msg": "Credenciais inválidas."}), 401

    tenant = user.tenant

    access_token = create_access_token(
        identity=user.id,
        additional_claims={
            "tenant_id": user.tenant_id,
            "plan": user.plan or tenant.plan if tenant else "BASIC",
        },
    )

    return (
        jsonify(
            {
                "access_token": access_token,
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "tenant_id": user.tenant_id,
                    "tenant_name": tenant.name if tenant else None,
                    "plan": user.plan or (tenant.plan if tenant else "BASIC"),
                },
            }
        ),
        200,
    )


@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    tenant_name = data.get("tenant_name", "Nova Oficina")

    if not all([name, email, password]):
        return jsonify({"msg": "Nome, email e senha são obrigatórios."}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email já está em uso."}), 409

    tenant = Tenant(name=tenant_name)
    db.session.add(tenant)
    db.session.flush()  # garante tenant.id

    user = User(
        name=name,
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
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "tenant_id": user.tenant_id,
            }
        ),
        201,
    )


@bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "Usuário não encontrado."}), 404

    tenant = user.tenant

    return (
        jsonify(
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "tenant_id": user.tenant_id,
                "tenant_name": tenant.name if tenant else None,
                "plan": user.plan or (tenant.plan if tenant else "BASIC"),
            }
        ),
        200,
    )
