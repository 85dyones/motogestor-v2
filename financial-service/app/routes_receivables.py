# financial-service/app/routes_receivables.py
from datetime import datetime, date
from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required
from .models import db, AccountReceivable, _to_decimal
from .utils import get_current_tenant_id, is_manager_or_owner

bp = Blueprint("receivables", __name__)


@bp.get("/")
@jwt_required()
def list_receivables():
    tenant_id = get_current_tenant_id()
    status = request.args.get("status")
    customer = request.args.get("customer")
    source_type = request.args.get("source_type")
    from_due = request.args.get("from_due")
    to_due = request.args.get("to_due")

    query = AccountReceivable.query.filter_by(tenant_id=tenant_id)

    if status:
        query = query.filter_by(status=status)
    if customer:
        like = f"%{customer}%"
        query = query.filter(AccountReceivable.customer_name.ilike(like))
    if source_type:
        query = query.filter_by(source_type=source_type)
    if from_due:
        query = query.filter(AccountReceivable.due_date >= date.fromisoformat(from_due))
    if to_due:
        query = query.filter(AccountReceivable.due_date <= date.fromisoformat(to_due))

    recs = query.order_by(AccountReceivable.due_date.asc()).all()

    return jsonify(
        [
            {
                "id": r.id,
                "source_type": r.source_type,
                "source_id": r.source_id,
                "customer_name": r.customer_name,
                "description": r.description,
                "issue_date": r.issue_date.isoformat() if r.issue_date else None,
                "due_date": r.due_date.isoformat() if r.due_date else None,
                "amount": float(r.amount),
                "status": r.status,
                "received_amount": float(r.received_amount or 0),
                "received_at": r.received_at.isoformat() if r.received_at else None,
                "payment_method": r.payment_method,
            }
            for r in recs
        ]
    )


@bp.get("/<int:rec_id>")
@jwt_required()
def get_receivable(rec_id):
    tenant_id = get_current_tenant_id()
    r = db.session.get(AccountReceivable, rec_id)
    if not r or r.tenant_id != tenant_id:
        abort(404)

    return jsonify(
        {
            "id": r.id,
            "source_type": r.source_type,
            "source_id": r.source_id,
            "customer_name": r.customer_name,
            "description": r.description,
            "issue_date": r.issue_date.isoformat() if r.issue_date else None,
            "due_date": r.due_date.isoformat() if r.due_date else None,
            "amount": float(r.amount),
            "status": r.status,
            "received_amount": float(r.received_amount or 0),
            "received_at": r.received_at.isoformat() if r.received_at else None,
            "payment_method": r.payment_method,
            "notes": r.notes,
        }
    )


@bp.post("/")
@jwt_required()
def create_receivable():
    """Cria conta a receber manual (não necessariamente ligada a OS)."""
    if not is_manager_or_owner():
        return jsonify({"error": "permissão negada"}), 403

    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    customer_name = data.get("customer_name")
    amount = data.get("amount")
    due_date = data.get("due_date")

    if not customer_name or amount is None or not due_date:
        return (
            jsonify({"error": "customer_name, amount e due_date são obrigatórios"}),
            400,
        )

    rec = AccountReceivable(
        tenant_id=tenant_id,
        source_type=data.get("source_type") or "MANUAL",
        source_id=data.get("source_id"),
        customer_name=customer_name,
        description=data.get("description"),
        issue_date=(
            date.fromisoformat(data.get("issue_date"))
            if data.get("issue_date")
            else date.today()
        ),
        due_date=date.fromisoformat(due_date),
        amount=_to_decimal(amount),
        notes=data.get("notes"),
    )
    db.session.add(rec)
    db.session.commit()

    return jsonify({"id": rec.id}), 201


@bp.post("/from-os")
@jwt_required()
def create_from_os():
    """
    Cria conta a receber vinculada a uma OS.
    Espera:
    {
      "service_order_id": 123,
      "customer_name": "...",
      "amount": 500.00,
      "description": "OS #123 - revisão completa",
      "due_date": "2025-12-20"
    }
    """
    if not is_manager_or_owner():
        return jsonify({"error": "permissão negada"}), 403

    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    so_id = data.get("service_order_id")
    customer_name = data.get("customer_name")
    amount = data.get("amount")
    due_date = data.get("due_date")

    if not all([so_id, customer_name, amount, due_date]):
        return (
            jsonify(
                {
                    "error": "service_order_id, customer_name, amount e due_date são obrigatórios"
                }
            ),
            400,
        )

    rec = AccountReceivable(
        tenant_id=tenant_id,
        source_type="OS",
        source_id=so_id,
        customer_name=customer_name,
        description=data.get("description") or f"OS #{so_id}",
        issue_date=date.today(),
        due_date=date.fromisoformat(due_date),
        amount=_to_decimal(amount),
    )
    db.session.add(rec)
    db.session.commit()

    return jsonify({"id": rec.id}), 201


@bp.patch("/<int:rec_id>")
@jwt_required()
def update_receivable(rec_id):
    if not is_manager_or_owner():
        return jsonify({"error": "permissão negada"}), 403

    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    rec = db.session.get(AccountReceivable, rec_id)
    if not rec or rec.tenant_id != tenant_id:
        abort(404)

    if "customer_name" in data:
        rec.customer_name = data["customer_name"]
    if "description" in data:
        rec.description = data["description"]
    if "issue_date" in data:
        rec.issue_date = (
            date.fromisoformat(data["issue_date"])
            if data["issue_date"]
            else rec.issue_date
        )
    if "due_date" in data:
        rec.due_date = (
            date.fromisoformat(data["due_date"]) if data["due_date"] else rec.due_date
        )
    if "amount" in data:
        rec.amount = _to_decimal(data["amount"])
    if "notes" in data:
        rec.notes = data["notes"]

    db.session.commit()

    return jsonify({"message": "recebível atualizado"})


@bp.patch("/<int:rec_id>/pay")
@jwt_required()
def pay_receivable(rec_id):
    """
    Dar baixa total ou parcial.
    Body:
    {
      "amount": 300.00,
      "payment_method": "PIX"
    }
    """
    if not is_manager_or_owner():
        return jsonify({"error": "permissão negada"}), 403

    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    amount = data.get("amount")
    payment_method = data.get("payment_method")

    if amount is None:
        return jsonify({"error": "amount é obrigatório"}), 400

    rec = db.session.get(AccountReceivable, rec_id)
    if not rec or rec.tenant_id != tenant_id:
        abort(404)

    pay_amount = _to_decimal(amount)
    new_received = _to_decimal(rec.received_amount) + pay_amount

    rec.received_amount = new_received
    rec.payment_method = payment_method or rec.payment_method
    rec.received_at = datetime.utcnow()

    if new_received >= _to_decimal(rec.amount):
        rec.status = "PAID"
    elif new_received > 0:
        rec.status = "PARTIAL"

    db.session.commit()

    return jsonify(
        {
            "message": "baixa registrada",
            "status": rec.status,
            "received_amount": float(rec.received_amount),
        }
    )


@bp.delete("/<int:rec_id>")
@jwt_required()
def cancel_receivable(rec_id):
    if not is_manager_or_owner():
        return jsonify({"error": "permissão negada"}), 403

    tenant_id = get_current_tenant_id()
    rec = db.session.get(AccountReceivable, rec_id)
    if not rec or rec.tenant_id != tenant_id:
        abort(404)

    rec.status = "CANCELLED"
    db.session.commit()

    return jsonify({"message": "recebível cancelado"})
