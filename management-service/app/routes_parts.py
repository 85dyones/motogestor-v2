# management-service/app/routes_parts.py
from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required
from .models import db, Part, StockMovement
from .utils import get_current_tenant_id, is_manager_or_owner

bp = Blueprint("parts", __name__)


@bp.get("/")
@jwt_required()
def list_parts():
    tenant_id = get_current_tenant_id()
    q = request.args.get("q")
    only_low = request.args.get("low_stock") == "1"

    query = Part.query.filter_by(tenant_id=tenant_id, is_active=True)
    if q:
        like = f"%{q}%"
        query = query.filter((Part.name.ilike(like)) | (Part.sku.ilike(like)))
    if only_low:
        query = query.filter(Part.quantity_in_stock <= Part.min_stock)

    parts = query.order_by(Part.name.asc()).all()

    return jsonify(
        [
            {
                "id": p.id,
                "sku": p.sku,
                "name": p.name,
                "unit_price": float(p.unit_price or 0),
                "quantity_in_stock": p.quantity_in_stock,
                "min_stock": p.min_stock,
            }
            for p in parts
        ]
    )


@bp.post("/")
@jwt_required()
def create_part():
    if not is_manager_or_owner():
        return jsonify({"error": "permissão negada"}), 403

    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    sku = data.get("sku")
    name = data.get("name")
    if not sku or not name:
        return jsonify({"error": "sku e name são obrigatórios"}), 400

    part = Part(
        tenant_id=tenant_id,
        sku=sku,
        name=name,
        unit_price=data.get("unit_price") or 0,
        quantity_in_stock=data.get("quantity_in_stock") or 0,
        min_stock=data.get("min_stock") or 0,
    )
    db.session.add(part)
    db.session.commit()

    return jsonify({"id": part.id, "name": part.name}), 201


@bp.patch("/<int:part_id>")
@jwt_required()
def update_part(part_id):
    if not is_manager_or_owner():
        return jsonify({"error": "permissão negada"}), 403

    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    part = db.session.get(Part, part_id)
    if not part or part.tenant_id != tenant_id or not part.is_active:
        abort(404)

    part.sku = data.get("sku", part.sku)
    part.name = data.get("name", part.name)
    if "unit_price" in data:
        part.unit_price = data["unit_price"]
    if "min_stock" in data:
        part.min_stock = data["min_stock"]

    db.session.commit()

    return jsonify({"message": "peça atualizada"})


@bp.post("/<int:part_id>/stock-movement")
@jwt_required()
def stock_movement(part_id):
    if not is_manager_or_owner():
        return jsonify({"error": "permissão negada"}), 403

    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    movement_type = data.get("movement_type")  # in | out | adjust
    quantity = data.get("quantity")
    reason = data.get("reason", "")
    related_order_id = data.get("related_order_id")

    if movement_type not in ("in", "out", "adjust"):
        return jsonify({"error": "movement_type inválido"}), 400
    if not quantity:
        return jsonify({"error": "quantity é obrigatório"}), 400

    part = db.session.get(Part, part_id)
    if not part or part.tenant_id != tenant_id or not part.is_active:
        abort(404)

    qty = int(quantity)

    if movement_type == "in":
        part.quantity_in_stock += qty
    elif movement_type == "out":
        if part.quantity_in_stock < qty:
            return jsonify({"error": "estoque insuficiente"}), 400
        part.quantity_in_stock -= qty
    else:  # adjust
        part.quantity_in_stock = qty

    movement = StockMovement(
        tenant_id=tenant_id,
        part_id=part.id,
        movement_type=movement_type,
        quantity=qty,
        reason=reason,
        related_order_id=related_order_id,
    )

    db.session.add(movement)
    db.session.commit()

    return jsonify({"message": "movimentação registrada", "stock": part.quantity_in_stock})


@bp.get("/<int:part_id>/movements")
@jwt_required()
def list_movements(part_id):
    tenant_id = get_current_tenant_id()

    part = db.session.get(Part, part_id)
    if not part or part.tenant_id != tenant_id or not part.is_active:
        abort(404)

    moves = (
        StockMovement.query.filter_by(tenant_id=tenant_id, part_id=part.id)
        .order_by(StockMovement.created_at.desc())
        .all()
    )

    return jsonify(
        [
            {
                "id": m.id,
                "movement_type": m.movement_type,
                "quantity": m.quantity,
                "reason": m.reason,
                "related_order_id": m.related_order_id,
                "created_at": m.created_at.isoformat(),
            }
            for m in moves
        ]
    )
