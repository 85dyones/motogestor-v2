# teamcrm-service/app/routes_staff.py
from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import jwt_required

from .models import Staff, db
from .utils import get_current_tenant_id, is_manager_or_owner

bp = Blueprint("staff", __name__)


@bp.get("/")
@jwt_required()
def list_staff():
    tenant_id = get_current_tenant_id()
    active = request.args.get("active")

    query = Staff.query.filter_by(tenant_id=tenant_id)
    if active == "1":
        query = query.filter_by(is_active=True)
    elif active == "0":
        query = query.filter_by(is_active=False)

    staff_list = query.order_by(Staff.name.asc()).all()

    return jsonify(
        [
            {
                "id": s.id,
                "name": s.name,
                "role": s.role,
                "phone": s.phone,
                "email": s.email,
                "is_active": s.is_active,
            }
            for s in staff_list
        ]
    )


@bp.get("/<int:staff_id>")
@jwt_required()
def get_staff(staff_id):
    tenant_id = get_current_tenant_id()
    s = db.session.get(Staff, staff_id)
    if not s or s.tenant_id != tenant_id:
        abort(404)

    return jsonify(
        {
            "id": s.id,
            "name": s.name,
            "role": s.role,
            "phone": s.phone,
            "email": s.email,
            "is_active": s.is_active,
        }
    )


@bp.post("/")
@jwt_required()
def create_staff():
    if not is_manager_or_owner():
        return jsonify({"error": "permissão negada"}), 403

    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    name = data.get("name")
    if not name:
        return jsonify({"error": "name é obrigatório"}), 400

    staff = Staff(
        tenant_id=tenant_id,
        name=name,
        role=data.get("role"),
        phone=data.get("phone"),
        email=data.get("email"),
    )
    db.session.add(staff)
    db.session.commit()

    return jsonify({"id": staff.id, "name": staff.name}), 201


@bp.patch("/<int:staff_id>")
@jwt_required()
def update_staff(staff_id):
    if not is_manager_or_owner():
        return jsonify({"error": "permissão negada"}), 403

    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    s = db.session.get(Staff, staff_id)
    if not s or s.tenant_id != tenant_id:
        abort(404)

    if "name" in data:
        s.name = data["name"]
    if "role" in data:
        s.role = data["role"]
    if "phone" in data:
        s.phone = data["phone"]
    if "email" in data:
        s.email = data["email"]
    if "is_active" in data:
        s.is_active = bool(data["is_active"])

    db.session.commit()

    return jsonify({"message": "colaborador atualizado"})
