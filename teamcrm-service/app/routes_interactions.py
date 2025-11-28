# teamcrm-service/app/routes_interactions.py
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from .models import Interaction, Staff, db
from .utils import get_current_tenant_id

bp = Blueprint("interactions", __name__)


@bp.get("/")
@jwt_required()
def list_interactions():
    tenant_id = get_current_tenant_id()

    customer_id = request.args.get("customer_id")
    related_order_id = request.args.get("related_order_id")
    channel = request.args.get("channel")
    staff_id = request.args.get("staff_id")
    limit = int(request.args.get("limit", 50))

    query = Interaction.query.filter_by(tenant_id=tenant_id)

    if customer_id:
        query = query.filter_by(customer_id=customer_id)
    if related_order_id:
        query = query.filter_by(related_order_id=related_order_id)
    if channel:
        query = query.filter_by(channel=channel)
    if staff_id:
        query = query.filter_by(staff_id=staff_id)

    interactions = query.order_by(Interaction.occurred_at.desc()).limit(limit).all()

    return jsonify(
        [
            {
                "id": i.id,
                "customer_id": i.customer_id,
                "related_order_id": i.related_order_id,
                "channel": i.channel,
                "direction": i.direction,
                "summary": i.summary,
                "details": i.details,
                "staff_id": i.staff_id,
                "staff_name": i.staff.name if i.staff else None,
                "occurred_at": i.occurred_at.isoformat(),
            }
            for i in interactions
        ]
    )


@bp.post("/")
@jwt_required()
def create_interaction():
    """
    Cria uma interação genérica (pode ser usada pelo frontend ou n8n).
    Body:
    {
      "customer_id": 10,
      "related_order_id": 123,
      "channel": "WHATSAPP",
      "direction": "OUT",
      "summary": "Enviado orçamento",
      "details": "Mensagem detalhada...",
      "staff_id": 3,
      "occurred_at": "2025-12-20T10:30:00"
    }
    """
    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    channel = data.get("channel")
    direction = data.get("direction") or "OUT"

    if not channel:
        return jsonify({"error": "channel é obrigatório"}), 400
    if direction not in ["IN", "OUT"]:
        return jsonify({"error": "direction deve ser IN ou OUT"}), 400

    staff_id = data.get("staff_id")
    staff = None
    if staff_id:
        staff = Staff.query.filter_by(
            id=staff_id, tenant_id=tenant_id, is_active=True
        ).first()
        if not staff:
            return jsonify({"error": "staff_id inválido"}), 400

    occurred_at = datetime.utcnow()
    if data.get("occurred_at"):
        occurred_at = datetime.fromisoformat(data["occurred_at"])

    inter = Interaction(
        tenant_id=tenant_id,
        customer_id=data.get("customer_id"),
        related_order_id=data.get("related_order_id"),
        channel=channel,
        direction=direction,
        summary=data.get("summary"),
        details=data.get("details"),
        staff_id=staff_id if staff else None,
        occurred_at=occurred_at,
    )

    db.session.add(inter)
    db.session.commit()

    return jsonify({"id": inter.id}), 201
