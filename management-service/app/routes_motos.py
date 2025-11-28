# management-service/app/routes_motos.py
from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import jwt_required

from .models import Customer, Motorcycle, db
from .utils import get_current_tenant_id

bp = Blueprint("motos", __name__)


@bp.get("/")
@jwt_required()
def list_motos():
    tenant_id = get_current_tenant_id()
    customer_id = request.args.get("customer_id")
    plate = request.args.get("plate")

    query = Motorcycle.query.filter_by(tenant_id=tenant_id, is_active=True)

    if customer_id:
        query = query.filter_by(customer_id=customer_id)
    if plate:
        query = query.filter(Motorcycle.plate.ilike(f"%{plate}%"))

    motos = query.all()

    return jsonify(
        [
            {
                "id": m.id,
                "customer_id": m.customer_id,
                "brand": m.brand,
                "model": m.model,
                "plate": m.plate,
                "year": m.year,
                "km_current": m.km_current,
            }
            for m in motos
        ]
    )


@bp.post("/")
@jwt_required()
def create_moto():
    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    customer_id = data.get("customer_id")
    if not customer_id:
        return jsonify({"error": "customer_id é obrigatório"}), 400

    customer = Customer.query.filter_by(
        id=customer_id, tenant_id=tenant_id, is_active=True
    ).first()
    if not customer:
        return jsonify({"error": "cliente inválido"}), 400

    moto = Motorcycle(
        tenant_id=tenant_id,
        customer_id=customer_id,
        brand=data.get("brand"),
        model=data.get("model"),
        plate=data.get("plate"),
        year=data.get("year"),
        km_current=data.get("km_current") or 0,
    )
    db.session.add(moto)
    db.session.commit()

    return jsonify({"id": moto.id, "plate": moto.plate}), 201


@bp.patch("/<int:moto_id>")
@jwt_required()
def update_moto(moto_id):
    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    moto = db.session.get(Motorcycle, moto_id)
    if not moto or moto.tenant_id != tenant_id or not moto.is_active:
        abort(404)

    moto.brand = data.get("brand", moto.brand)
    moto.model = data.get("model", moto.model)
    moto.plate = data.get("plate", moto.plate)
    moto.year = data.get("year", moto.year)
    if "km_current" in data:
        moto.km_current = data["km_current"]

    db.session.commit()

    return jsonify({"message": "moto atualizada"})


@bp.delete("/<int:moto_id>")
@jwt_required()
def delete_moto(moto_id):
    tenant_id = get_current_tenant_id()

    moto = db.session.get(Motorcycle, moto_id)
    if not moto or moto.tenant_id != tenant_id or not moto.is_active:
        abort(404)

    moto.is_active = False
    db.session.commit()

    return jsonify({"message": "moto desativada"})
