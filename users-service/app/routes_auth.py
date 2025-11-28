from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, get_jwt, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash

from .models import db, User, Tenant
from .identity import build_token
from .schemas import AuthResponse, AuthUser, LoginRequest, RegisterRequest
from .errors import ConflictError, NotFoundError, ValidationError

bp = Blueprint("auth_routes", __name__)


@bp.route("/login", methods=["POST"])
def login():
    try:
        payload = LoginRequest.model_validate(request.get_json() or {})
    except Exception as e:
        raise ValidationError("Email e senha são obrigatórios.", {"error": str(e)})

    user = User.query.filter_by(email=payload.email).first()
    if not user or not check_password_hash(user.password_hash, payload.password):
        raise ValidationError("Credenciais inválidas.")

    tenant = user.tenant

    access_token = build_token(
        identity=user.id,
        tenant_id=user.tenant_id,
        plan=user.plan or tenant.plan if tenant else "BASIC",
        tenant_name=tenant.name if tenant else None,
    )

    response = AuthResponse(
        access_token=access_token,
        user=AuthUser(
            id=user.id,
            name=user.name,
            email=user.email,
            tenant_id=user.tenant_id,
            tenant_name=tenant.name if tenant else None,
            plan=user.plan or (tenant.plan if tenant else "BASIC"),
            role=user.role,
        ),
    )

    return jsonify(response.model_dump()), 200


@bp.route("/register", methods=["POST"])
def register():
    try:
        payload = RegisterRequest.model_validate(request.get_json() or {})
    except Exception as e:
        raise ValidationError("Dados de cadastro inválidos.", {"error": str(e)})

    if User.query.filter_by(email=payload.email).first():
        raise ConflictError("Email já está em uso.")

    tenant = Tenant(name=payload.tenant_name)
    db.session.add(tenant)
    db.session.flush()  # garante tenant.id

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=generate_password_hash(payload.password),
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
    user_id = int(user_id) if user_id is not None else None
    user = db.session.get(User, user_id)
    token_claims = get_jwt()
    token_tenant_id = token_claims.get("tenant_id") if token_claims else None

    if not user or (token_tenant_id and user.tenant_id != token_tenant_id):
        raise NotFoundError("Usuário não encontrado para o tenant atual.")

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
