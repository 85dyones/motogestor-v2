# teamcrm-service/app/routes_tasks.py
from datetime import date, datetime
from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required
from .models import db, Task, Staff
from .utils import get_current_tenant_id, is_manager_or_owner

bp = Blueprint("tasks", __name__)


@bp.get("/")
@jwt_required()
def list_tasks():
    tenant_id = get_current_tenant_id()

    status = request.args.get("status")
    assigned_to_id = request.args.get("assigned_to_id")
    related_order_id = request.args.get("related_order_id")
    due_until = request.args.get("due_until")  # YYYY-MM-DD
    only_open = request.args.get("only_open") == "1"

    query = Task.query.filter_by(tenant_id=tenant_id)

    if status:
        query = query.filter_by(status=status)
    if assigned_to_id:
        query = query.filter_by(assigned_to_id=assigned_to_id)
    if related_order_id:
        query = query.filter_by(related_order_id=related_order_id)
    if due_until:
        query = query.filter(Task.due_date <= date.fromisoformat(due_until))
    if only_open:
        query = query.filter(Task.status.in_(["OPEN", "IN_PROGRESS", "WAITING"]))

    tasks = query.order_by(Task.due_date.asc().nulls_last(), Task.created_at.desc()).all()

    return jsonify(
        [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "assigned_to_id": t.assigned_to_id,
                "assigned_to_name": t.assigned_to.name if t.assigned_to else None,
                "related_order_id": t.related_order_id,
                "customer_id": t.customer_id,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "created_at": t.created_at.isoformat(),
            }
            for t in tasks
        ]
    )


@bp.get("/<int:task_id>")
@jwt_required()
def get_task(task_id):
    tenant_id = get_current_tenant_id()
    t = db.session.get(Task, task_id)
    if not t or t.tenant_id != tenant_id:
        abort(404)

    return jsonify(
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "status": t.status,
            "priority": t.priority,
            "assigned_to_id": t.assigned_to_id,
            "assigned_to_name": t.assigned_to.name if t.assigned_to else None,
            "related_order_id": t.related_order_id,
            "customer_id": t.customer_id,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "created_at": t.created_at.isoformat(),
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        }
    )


@bp.post("/")
@jwt_required()
def create_task():
    """
    Cria tarefa geral ou ligada a uma OS/cliente.

    Body:
    {
      "title": "...",  (obrigatório)
      "description": "...",
      "priority": "NORMAL",
      "assigned_to_id": 3,
      "related_order_id": 123,
      "customer_id": 10,
      "due_date": "2025-12-20"
    }
    """
    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    title = data.get("title")
    if not title:
        return jsonify({"error": "title é obrigatório"}), 400

    assigned_to_id = data.get("assigned_to_id")
    staff = None
    if assigned_to_id:
        staff = Staff.query.filter_by(
            id=assigned_to_id, tenant_id=tenant_id, is_active=True
        ).first()
        if not staff:
            return jsonify({"error": "assigned_to_id inválido"}), 400

    due_date = None
    if data.get("due_date"):
        due_date = date.fromisoformat(data["due_date"])

    task = Task(
        tenant_id=tenant_id,
        title=title,
        description=data.get("description"),
        priority=data.get("priority") or "NORMAL",
        assigned_to_id=assigned_to_id if staff else None,
        related_order_id=data.get("related_order_id"),
        customer_id=data.get("customer_id"),
        due_date=due_date,
    )
    db.session.add(task)
    db.session.commit()

    return jsonify({"id": task.id}), 201


@bp.patch("/<int:task_id>")
@jwt_required()
def update_task(task_id):
    tenant_id = get_current_tenant_id()
    data = request.get_json() or {}

    # Edição geral: dono/gerente; o próprio responsável pode mexer no status
    # mas pra simplificar, vamos exigir PERMISSÃO só em mudanças sensíveis.
    t = db.session.get(Task, task_id)
    if not t or t.tenant_id != tenant_id:
        abort(404)

    # Controles básicos de permissão
    change_assignment = any(
        key in data for key in ("assigned_to_id", "customer_id", "related_order_id")
    )
    change_title_scope = any(key in data for key in ("title", "description", "priority"))

    if change_assignment or change_title_scope:
        if not is_manager_or_owner():
            return jsonify({"error": "apenas owner/manager podem alterar tarefa desse jeito"}), 403

    if "title" in data:
        t.title = data["title"]
    if "description" in data:
        t.description = data["description"]
    if "priority" in data:
        t.priority = data["priority"]

    if "assigned_to_id" in data:
        assigned_to_id = data["assigned_to_id"]
        if assigned_to_id is None:
            t.assigned_to_id = None
        else:
            staff = Staff.query.filter_by(
                id=assigned_to_id, tenant_id=tenant_id, is_active=True
            ).first()
            if not staff:
                return jsonify({"error": "assigned_to_id inválido"}), 400
            t.assigned_to_id = assigned_to_id

    if "related_order_id" in data:
        t.related_order_id = data["related_order_id"]
    if "customer_id" in data:
        t.customer_id = data["customer_id"]

    if "due_date" in data:
        dd = data["due_date"]
        t.due_date = date.fromisoformat(dd) if dd else None

    if "status" in data:
        new_status = data["status"]
        if new_status not in ["OPEN", "IN_PROGRESS", "WAITING", "DONE", "CANCELLED"]:
            return jsonify({"error": "status inválido"}), 400
        t.status = new_status
        if new_status == "DONE":
            t.completed_at = datetime.utcnow()

    db.session.commit()

    return jsonify({"message": "tarefa atualizada"})
