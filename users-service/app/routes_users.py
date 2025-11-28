from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from .models import User

bp = Blueprint("users_routes", __name__)


@bp.route("/", methods=["GET"])
@jwt_required()
def list_users():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user:
        return jsonify({"msg": "Usuário não encontrado."}), 404

    users = User.query.filter_by(tenant_id=current_user.tenant_id).all()

    return jsonify(
        [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "tenant_id": u.tenant_id,
                "role": u.role,
                "plan": u.plan,
            }
            for u in users
        ]
    )
