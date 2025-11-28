# management-service/app/routes_customers.py
from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import jwt_required

from .models import Customer, db
from .utils import get_current_tenant_id, is_manager_or_owner

bp = Blueprint("customers", __name__)


@bp.get("/")
@jwt_required()
def list_customers():
    tenant_id = get_current_tenant_id()
    q = request.args.get("q")

    query = Customer.query.filter_by(tenant_id=tenant_id, is_active=True)
    if q:
        like = f"%{q}%"
        query = query.filter(Customer.name.ilike(like))

    customers = query.order_by(Customer.created_at.desc()).all()

    return jsonify(
        [
            {
                "id": c.id,
                "name": c.name,
                "phone": c.phone,
                "email": c.email,
                "document": c.document,
                "notes": c.notes,
            }
            for c in customers
        ]
    )


@bp.get("/<int:customer_id>")
@jwt_required()
def get_customer(customer_id):
    tenant_id = get_current_tenant_id()
    customer = db.session.get(Customer, customer_id)
    if not customer or customer.tenant_id != tenant_id or not customer.is_active:
        abort(404)

    return jsonify(
        {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "email": customer.email,
            "document": customer.document,
            "notes": customer.notes,
        }
    )


@bp.post("/")
@jwt_required()
def create_customer():
    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    name = data.get("name")
    if not name:
        return jsonify({"error": "name é obrigatório"}), 400

    customer = Customer(
        tenant_id=tenant_id,
        name=name,
        phone=data.get("phone"),
        email=data.get("email"),
        document=data.get("document"),
        notes=data.get("notes"),
    )
    db.session.add(customer)
    db.session.commit()

    return jsonify({"id": customer.id, "name": customer.name}), 201


@bp.patch("/<int:customer_id>")
@jwt_required()
def update_customer(customer_id):
    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    customer = db.session.get(Customer, customer_id)
    if not customer or customer.tenant_id != tenant_id or not customer.is_active:
        abort(404)

    customer.name = data.get("name", customer.name)
    customer.phone = data.get("phone", customer.phone)
    customer.email = data.get("email", customer.email)
    customer.document = data.get("document", customer.document)
    customer.notes = data.get("notes", customer.notes)

    db.session.commit()

    return jsonify({"message": "cliente atualizado"})


@bp.delete("/<int:customer_id>")
@jwt_required()
def delete_customer(customer_id):
    if not is_manager_or_owner():
        return jsonify({"error": "permissão negada"}), 403

    tenant_id = get_current_tenant_id()
    customer = db.session.get(Customer, customer_id)
    if not customer or customer.tenant_id != tenant_id or not customer.is_active:
        abort(404)

    customer.is_active = False
    db.session.commit()

    return jsonify({"message": "cliente desativado"})
