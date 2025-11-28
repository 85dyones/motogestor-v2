# api-gateway/app/routes_services.py
from flask import Blueprint
from .config import (
    MANAGEMENT_SERVICE_URL,
    FINANCIAL_SERVICE_URL,
    TEAMCRM_SERVICE_URL,
    AI_SERVICE_URL,
)
from .proxy import forward_request

bp = Blueprint("services_proxy", __name__)

ALL_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]


# MANAGEMENT: /management/... -> management-service
@bp.route("/management", defaults={"path": ""}, methods=ALL_METHODS)
@bp.route("/management/<path:path>", methods=ALL_METHODS)
def management_proxy(path: str):
    """
    /management/customers -> management-service /customers
    /management/os/123    -> management-service /os/123
    """
    return forward_request(MANAGEMENT_SERVICE_URL, path)


# FINANCIAL: /financial/... -> financial-service
@bp.route("/financial", defaults={"path": ""}, methods=ALL_METHODS)
@bp.route("/financial/<path:path>", methods=ALL_METHODS)
def financial_proxy(path: str):
    """
    /financial/receivables -> financial-service /receivables
    /financial/payables    -> financial-service /payables
    """
    return forward_request(FINANCIAL_SERVICE_URL, path)


# TEAMCRM: /teamcrm/... -> teamcrm-service
@bp.route("/teamcrm", defaults={"path": ""}, methods=ALL_METHODS)
@bp.route("/teamcrm/<path:path>", methods=ALL_METHODS)
def teamcrm_proxy(path: str):
    """
    /teamcrm/staff -> teamcrm-service /staff
    /teamcrm/tasks -> teamcrm-service /tasks
    """
    return forward_request(TEAMCRM_SERVICE_URL, path)


# AI: /ai/... -> ai-service /ai/...
@bp.route("/ai", defaults={"path": ""}, methods=ALL_METHODS)
@bp.route("/ai/<path:path>", methods=ALL_METHODS)
def ai_proxy(path: str):
    """
    Externamente: /ai/whatsapp/generate-message
    Internamente: ai-service /ai/whatsapp/generate-message
    """
    subpath = f"ai/{path}" if path else "ai"
    return forward_request(AI_SERVICE_URL, subpath)
