from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from .errors import NotFoundError
from .models import db, User
from .schemas import UserOut
from .tenant import tenant_query

bp = Blueprint("users_routes", __name__)


@bp.route("/", methods=["GET"])
@jwt_required()
def list_users():
    current_user_id = get_jwt_identity()
    current_user_id = int(current_user_id) if current_user_id is not None else None
    current_user = db.session.get(User, current_user_id)
    if not current_user:
        raise NotFoundError("Usuário não encontrado.")

    users = tenant_query(User).all()

    return jsonify(
        [
            UserOut(
                **{
                    "id": u.id,
                    "name": u.name,
                    "email": u.email,
                    "tenant_id": u.tenant_id,
                    "role": u.role,
                    "plan": u.plan,
                }
            ).model_dump()
            for u in users
        ]
    )
