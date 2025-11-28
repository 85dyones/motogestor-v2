# financial-service/app/routes_cashflow.py
from datetime import date
from decimal import Decimal
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from .models import AccountReceivable, AccountPayable, _to_decimal
from .utils import get_current_tenant_id

bp = Blueprint("cashflow", __name__)


@bp.get("/summary")
@jwt_required()
def cashflow_summary():
    """
    Resumo simples de caixa por período.
    Query params:
      start=YYYY-MM-DD
      end=YYYY-MM-DD
    """
    tenant_id = get_current_tenant_id()
    start_str = request.args.get("start")
    end_str = request.args.get("end")

    if not start_str or not end_str:
        return jsonify({"error": "start e end são obrigatórios (YYYY-MM-DD)"}), 400

    start = date.fromisoformat(start_str)
    end = date.fromisoformat(end_str)

    # Entradas: recebíveis com status PAID / PARTIAL dentro do período de recebimento
    recs = (
        AccountReceivable.query.filter(
            AccountReceivable.tenant_id == tenant_id,
            AccountReceivable.received_at.isnot(None),
            AccountReceivable.received_at >= start,
            AccountReceivable.received_at <= end,
        ).all()
    )

    # Saídas: pagáveis com status PAID / PARTIAL dentro do período de pagamento
    pays = (
        AccountPayable.query.filter(
            AccountPayable.tenant_id == tenant_id,
            AccountPayable.paid_at.isnot(None),
            AccountPayable.paid_at >= start,
            AccountPayable.paid_at <= end,
        ).all()
    )

    total_in = Decimal("0.00")
    total_out = Decimal("0.00")

    for r in recs:
        total_in += _to_decimal(r.received_amount)

    for p in pays:
        total_out += _to_decimal(p.paid_amount)

    net = total_in - total_out

    return jsonify(
        {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "total_in": float(total_in),
            "total_out": float(total_out),
            "net": float(net),
        }
    )
