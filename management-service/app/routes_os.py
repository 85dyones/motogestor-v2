# management-service/app/routes_os.py
from datetime import datetime
from decimal import Decimal

from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import jwt_required

from .models import (Customer, Motorcycle, Part, ServiceItem, ServiceOrder,
                     StockMovement, db, recalc_order_totals)
from .observability import OS_CREATED_COUNTER
from .utils import get_current_tenant_id, is_manager_or_owner
from .tenant_guard import tenant_guard

bp = Blueprint("os", __name__)


@bp.get("/")
@jwt_required()
def list_os():
    tenant_id = get_current_tenant_id()
    status = request.args.get("status")
    customer_id = request.args.get("customer_id")

    query = ServiceOrder.query.filter_by(tenant_id=tenant_id)

    if status:
        query = query.filter_by(status=status)
    if customer_id:
        query = query.filter_by(customer_id=customer_id)

    orders = query.order_by(ServiceOrder.created_at.desc()).all()

    def _serialize_order(o: ServiceOrder):
        return {
            "id": o.id,
            "status": o.status,
            "customer": o.customer.name if o.customer else None,
            "customer_id": o.customer_id,
            "motorcycle_id": o.motorcycle_id,
            "motorcycle_plate": o.motorcycle.plate if o.motorcycle else None,
            "description": o.description,
            "total_parts": float(o.total_parts or 0),
            "total_labor": float(o.total_labor or 0),
            "total_amount": float(o.total_amount or 0),
            "created_at": o.created_at.isoformat(),
            "scheduled_date": (
                o.scheduled_date.isoformat() if o.scheduled_date else None
            ),
            "closed_at": o.closed_at.isoformat() if o.closed_at else None,
        }

    return jsonify([_serialize_order(o) for o in orders])


@bp.get("/<int:order_id>")
@jwt_required()
def get_os(order_id):
    tenant_id = get_current_tenant_id()
    order = db.session.get(ServiceOrder, order_id)
    if not order or order.tenant_id != tenant_id:
        abort(404)

    items = [
        {
            "id": i.id,
            "item_type": i.item_type,
            "part_id": i.part_id,
            "description": i.description,
            "quantity": float(i.quantity or 0),
            "unit_price": float(i.unit_price or 0),
            "total": float(i.total or 0),
        }
        for i in order.items
    ]

    return jsonify(
        {
            "id": order.id,
            "status": order.status,
            "customer_id": order.customer_id,
            "motorcycle_id": order.motorcycle_id,
            "description": order.description,
            "total_parts": float(order.total_parts or 0),
            "total_labor": float(order.total_labor or 0),
            "total_amount": float(order.total_amount or 0),
            "items": items,
        }
    )


@bp.post("/")
@jwt_required()
@tenant_guard(body_keys=("tenant_id",))
def create_os():
    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    customer_id = data.get("customer_id")
    motorcycle_id = data.get("motorcycle_id")
    description = data.get("description", "")
    scheduled_date_str = data.get("scheduled_date")

    if not customer_id or not motorcycle_id:
        return jsonify({"error": "customer_id e motorcycle_id são obrigatórios"}), 400

    customer = Customer.query.filter_by(
        id=customer_id, tenant_id=tenant_id, is_active=True
    ).first()
    moto = Motorcycle.query.filter_by(
        id=motorcycle_id, tenant_id=tenant_id, is_active=True
    ).first()

    if not customer or not moto:
        return jsonify({"error": "cliente ou moto inválidos"}), 400

    scheduled_date = None
    if scheduled_date_str:
        scheduled_date = datetime.fromisoformat(scheduled_date_str)

    order = ServiceOrder(
        tenant_id=tenant_id,
        customer_id=customer_id,
        motorcycle_id=motorcycle_id,
        description=description,
        scheduled_date=scheduled_date,
    )
    db.session.add(order)
    db.session.commit()
    OS_CREATED_COUNTER.labels(tenant_id=str(tenant_id)).inc()

    return jsonify({"id": order.id, "status": order.status}), 201


@bp.patch("/<int:order_id>")
@jwt_required()
@tenant_guard(path_key="tenant_id", body_keys=("tenant_id",))
def update_os(order_id):
    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    order = db.session.get(ServiceOrder, order_id)
    if not order or order.tenant_id != tenant_id:
        abort(404)

    if "description" in data:
        order.description = data["description"]
    if "scheduled_date" in data:
        sd = data["scheduled_date"]
        order.scheduled_date = datetime.fromisoformat(sd) if sd else None

    db.session.commit()

    return jsonify({"message": "OS atualizada"})


@bp.patch("/<int:order_id>/status")
@jwt_required()
@tenant_guard(path_key="tenant_id", body_keys=("tenant_id",))
def update_os_status(order_id):
    if not is_manager_or_owner():
        return jsonify({"error": "permissão negada"}), 403

    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}
    new_status = data.get("status")

    if new_status not in [
        "OPEN",
        "IN_PROGRESS",
        "WAITING_PARTS",
        "COMPLETED",
        "CANCELLED",
    ]:
        return jsonify({"error": "status inválido"}), 400

    order = db.session.get(ServiceOrder, order_id)
    if not order or order.tenant_id != tenant_id:
        abort(404)

    order.status = new_status
    if new_status == "COMPLETED":
        order.closed_at = datetime.utcnow()

    db.session.commit()

    return jsonify({"message": "status atualizado"})


@bp.post("/<int:order_id>/items")
@jwt_required()
@tenant_guard(path_key="tenant_id", body_keys=("tenant_id",))
def add_os_item(order_id):
    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    item_type = data.get("item_type")  # part | labor
    description = data.get("description", "")
    quantity = Decimal(str(data.get("quantity", 1)))
    unit_price = Decimal(str(data.get("unit_price", 0)))
    part_id = data.get("part_id")

    if item_type not in ("part", "labor"):
        return jsonify({"error": "item_type deve ser 'part' ou 'labor'"}), 400

    order = db.session.get(ServiceOrder, order_id)
    if not order or order.tenant_id != tenant_id:
        abort(404)

    part = None
    if item_type == "part":
        if not part_id:
            return jsonify({"error": "part_id é obrigatório para itens de peça"}), 400
        part = Part.query.filter_by(
            id=part_id, tenant_id=tenant_id, is_active=True
        ).first()
        if not part:
            return jsonify({"error": "peça inválida"}), 400

        qty_int = int(quantity)
        if part.quantity_in_stock < qty_int:
            return jsonify({"error": "estoque insuficiente"}), 400

        # baixa estoque
        part.quantity_in_stock -= qty_int
        movement = StockMovement(
            tenant_id=tenant_id,
            part_id=part.id,
            movement_type="out",
            quantity=qty_int,
            reason=f"Uso na OS #{order.id}",
            related_order_id=order.id,
        )
        db.session.add(movement)

    total = quantity * unit_price

    item = ServiceItem(
        tenant_id=tenant_id,
        service_order_id=order.id,
        item_type=item_type,
        part_id=part.id if part else None,
        description=description or (part.name if part else ""),
        quantity=quantity,
        unit_price=unit_price,
        total=total,
    )
    db.session.add(item)

    # recalcula totais
    recalc_order_totals(order)

    db.session.commit()

    return (
        jsonify(
            {
                "id": item.id,
                "item_type": item.item_type,
                "description": item.description,
                "quantity": float(item.quantity or 0),
                "unit_price": float(item.unit_price or 0),
                "total": float(item.total or 0),
                "order_totals": {
                    "total_parts": float(order.total_parts or 0),
                    "total_labor": float(order.total_labor or 0),
                    "total_amount": float(order.total_amount or 0),
                },
            }
        ),
        201,
    )


@bp.patch("/<int:order_id>/items/<int:item_id>")
@jwt_required()
def update_os_item(order_id, item_id):
    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    order = db.session.get(ServiceOrder, order_id)
    if not order or order.tenant_id != tenant_id:
        abort(404)
    item = db.session.get(ServiceItem, item_id)
    if not item or item.tenant_id != tenant_id or item.service_order_id != order.id:
        abort(404)

    # não vamos tentar reverter estoque automaticamente pra não virar caos,
    # ajustes de quantidade de peça grandes o dono faz via tela de estoque

    if "description" in data:
        item.description = data["description"]
    if "quantity" in data:
        item.quantity = Decimal(str(data["quantity"]))
    if "unit_price" in data:
        item.unit_price = Decimal(str(data["unit_price"]))

    item.total = (item.quantity or 0) * (item.unit_price or 0)

    recalc_order_totals(order)
    db.session.commit()

    return jsonify({"message": "item atualizado"})


@bp.delete("/<int:order_id>/items/<int:item_id>")
@jwt_required()
def delete_os_item(order_id, item_id):
    tenant_id = get_current_tenant_id()

    order = db.session.get(ServiceOrder, order_id)
    if not order or order.tenant_id != tenant_id:
        abort(404)
    item = db.session.get(ServiceItem, item_id)
    if not item or item.tenant_id != tenant_id or item.service_order_id != order.id:
        abort(404)

    # opcional: não devolver estoque automático pra não confundir controle
    db.session.delete(item)
    recalc_order_totals(order)
    db.session.commit()

    return jsonify({"message": "item removido"})
