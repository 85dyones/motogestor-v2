# teamcrm-service/app/routes_dashboard.py
from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from .models import Interaction, Task
from .utils import get_current_tenant_id

bp = Blueprint("dashboard", __name__)


@bp.get("/summary")
@jwt_required()
def summary():
    """
    Resumo simples de produtividade da equipe.

    Query params opcionais:
      days (default=7) -> janela usada pra contar interações recentes
    """
    tenant_id = get_current_tenant_id()
    days = int(request.args.get("days", 7))

    today = date.today()
    start_date = today - timedelta(days=days)

    # Tarefas
    open_tasks = Task.query.filter(
        Task.tenant_id == tenant_id,
        Task.status.in_(["OPEN", "IN_PROGRESS", "WAITING"]),
    ).count()
    late_tasks = Task.query.filter(
        Task.tenant_id == tenant_id,
        Task.status.in_(["OPEN", "IN_PROGRESS", "WAITING"]),
        Task.due_date.isnot(None),
        Task.due_date < today,
    ).count()
    done_tasks_period = Task.query.filter(
        Task.tenant_id == tenant_id,
        Task.status == "DONE",
        Task.completed_at.isnot(None),
        Task.completed_at >= datetime.combine(start_date, datetime.min.time()),
    ).count()

    # Interações
    recent_interactions = Interaction.query.filter(
        Interaction.tenant_id == tenant_id,
        Interaction.occurred_at >= datetime.combine(start_date, datetime.min.time()),
    ).count()

    whatsapp_interactions = Interaction.query.filter(
        Interaction.tenant_id == tenant_id,
        Interaction.channel == "WHATSAPP",
        Interaction.occurred_at >= datetime.combine(start_date, datetime.min.time()),
    ).count()

    return jsonify(
        {
            "period_days": days,
            "tasks": {
                "open": open_tasks,
                "late": late_tasks,
                "done_in_period": done_tasks_period,
            },
            "interactions": {
                "total_in_period": recent_interactions,
                "whatsapp_in_period": whatsapp_interactions,
            },
        }
    )
