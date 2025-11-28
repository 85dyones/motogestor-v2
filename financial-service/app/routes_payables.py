# financial-service/app/routes_payables.py
from datetime import datetime, date
from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required
from .models import db, AccountPayable, _to_decimal
from .utils import get_current_tenant_id, is_manager_or_owner

bp = Blueprint("payables", __name__)


@bp.get("/")
@jwt_required()
def list_payables():
    tenant_id = get_current_tenant_id()
    status = request.args.get("status")
    supplier = request.args.get("supplier")
    category = request.args.get("category")
    from_due = request.args.get("from_due")
    to_due = request.args.get("to_due")

    query = AccountPayable.query.filter_by(tenant_id=tenant_id)

    if status:
        query = query.filter_by(status=status)
    if supplier:
        like = f"%{supplier}%"
        query = query.filter(AccountPayable.supplier_name.ilike(like))
    if category:
        query = query.filter_by(category=category)
    if from_due:
        query = query.filter(AccountPayable.due_date >= date.fromisoformat(from_due))
    if to_due:
        query = query.filter(AccountPayable.due_date <= date.fromisoformat(to_due))

    pays = query.order_by(AccountPayable.due_date.asc()).all()

    return jsonify(
        [
            {
                "id": p.id,
                "supplier_name": p.supplier_name,
                "description": p.description,
                "category": p.category,
                "issue_date": p.issue_date.isoformat() if p.issue_date else None,
                "due_date": p.due_date.isoformat() if p.due_date else None,
                "amount": float(p.amount),
                "status": p.status,
                "paid_amount": float(p.paid_amount or 0),
                "paid_at": p.paid_at.isoformat() if p.paid_at else None,
                "payment_method": p.payment_method,
            }
            for p in pays
        ]
    )


@bp.get("/<int:pay_id>")
@jwt_required()
def get_payable(pay_id):
    tenant_id = get_current_tenant_id()
    p = db.session.get(AccountPayable, pay_id)
    if not p or p.tenant_id != tenant_id:
        abort(404)

    return jsonify(
        {
            "id": p.id,
            "supplier_name": p.supplier_name,
            "description": p.description,
            "category": p.category,
            "issue_date": p.issue_date.isoformat() if p.issue_date else None,
            "due_date": p.due_date.isoformat() if p.due_date else None,
            "amount": float(p.amount),
            "status": p.status,
            "paid_amount": float(p.paid_amount or 0),
            "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            "payment_method": p.payment_method,
            "notes": p.notes,
        }
    )


@bp.post("/")
@jwt_required()
def create_payable():
    if not is_manager_or_owner():
        return jsonify({"error": "permissão negada"}), 403

    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    supplier_name = data.get("supplier_name")
    amount = data.get("amount")
    due_date = data.get("due_date")

    if not supplier_name or amount is None or not due_date:
        return jsonify({"error": "supplier_name, amount e due_date são obrigatórios"}), 400

    pay = AccountPayable(
        tenant_id=tenant_id,
        supplier_name=supplier_name,
        description=data.get("description"),
        category=data.get("category") or "OTHER",
        issue_date=date.fromisoformat(data.get("issue_date")) if data.get("issue_date") else date.today(),
        due_date=date.fromisoformat(due_date),
        amount=_to_decimal(amount),
        notes=data.get("notes"),
    )
    db.session.add(pay)
    db.session.commit()

    return jsonify({"id": pay.id}), 201


@bp.patch("/<int:pay_id>")
@jwt_required()
def update_payable(pay_id):
    if not is_manager_or_owner():
        return jsonify({"error": "permissão negada"}), 403

    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    pay = db.session.get(AccountPayable, pay_id)
    if not pay or pay.tenant_id != tenant_id:
        abort(404)

    if "supplier_name" in data:
        pay.supplier_name = data["supplier_name"]
    if "description" in data:
        pay.description = data["description"]
    if "category" in data:
        pay.category = data["category"]
    if "issue_date" in data:
        pay.issue_date = date.fromisoformat(data["issue_date"]) if data["issue_date"] else pay.issue_date
    if "due_date" in data:
        pay.due_date = date.fromisoformat(data["due_date"]) if data["due_date"] else pay.due_date
    if "amount" in data:
        pay.amount = _to_decimal(data["amount"])
    if "notes" in data:
        pay.notes = data["notes"]

    db.session.commit()

    return jsonify({"message": "pagável atualizado"})


@bp.patch("/<int:pay_id>/pay")
@jwt_required()
def pay_payable(pay_id):
    """
    Pagar total ou parcial.
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

    pay = db.session.get(AccountPayable, pay_id)
    if not pay or pay.tenant_id != tenant_id:
        abort(404)

    pay_amount = _to_decimal(amount)
    new_paid = _to_decimal(pay.paid_amount) + pay_amount

    pay.paid_amount = new_paid
    pay.payment_method = payment_method or pay.payment_method
    pay.paid_at = datetime.utcnow()

    if new_paid >= _to_decimal(pay.amount):
        pay.status = "PAID"
    elif new_paid > 0:
        pay.status = "PARTIAL"

    db.session.commit()

    return jsonify(
        {
            "message": "pagamento registrado",
            "status": pay.status,
            "paid_amount": float(pay.paid_amount),
        }
    )


@bp.delete("/<int:pay_id>")
@jwt_required()
def cancel_payable(pay_id):
    if not is_manager_or_owner():
        return jsonify({"error": "permissão negada"}), 403

    tenant_id = get_current_tenant_id()
    pay = db.session.get(AccountPayable, pay_id)
    if not pay or pay.tenant_id != tenant_id:
        abort(404)

    pay.status = "CANCELLED"
    db.session.commit()

    return jsonify({"message": "pagável cancelado"})
