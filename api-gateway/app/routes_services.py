# api-gateway/app/routes_services.py
from flask import Blueprint

from .config import load_config
from .proxy import forward_request

bp = Blueprint("services_proxy", __name__)
cfg = load_config()

ALL_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]


# MANAGEMENT: /management/... -> management-service
@bp.route("/management", defaults={"path": ""}, methods=ALL_METHODS)
@bp.route("/management/<path:path>", methods=ALL_METHODS)
def management_proxy(path: str):
    """
    /management/customers -> management-service /customers
    /management/os/123    -> management-service /os/123
    """
    return forward_request(cfg.management_service_url, path)


# FINANCIAL: /financial/... -> financial-service
@bp.route("/financial", defaults={"path": ""}, methods=ALL_METHODS)
@bp.route("/financial/<path:path>", methods=ALL_METHODS)
def financial_proxy(path: str):
    """
    /financial/receivables -> financial-service /receivables
    /financial/payables    -> financial-service /payables
    """
    return forward_request(cfg.financial_service_url, path)


# TEAMCRM: /teamcrm/... -> teamcrm-service
@bp.route("/teamcrm", defaults={"path": ""}, methods=ALL_METHODS)
@bp.route("/teamcrm/<path:path>", methods=ALL_METHODS)
def teamcrm_proxy(path: str):
    """
    /teamcrm/staff -> teamcrm-service /staff
    /teamcrm/tasks -> teamcrm-service /tasks
    """
    return forward_request(cfg.teamcrm_service_url, path)


# AI: /ai/... -> ai-service /ai/...
@bp.route("/ai", defaults={"path": ""}, methods=ALL_METHODS)
@bp.route("/ai/<path:path>", methods=ALL_METHODS)
def ai_proxy(path: str):
    """
    Externamente: /ai/whatsapp/generate-message
    Internamente: ai-service /ai/whatsapp/generate-message
    """
    subpath = f"ai/{path}" if path else "ai"
    return forward_request(cfg.ai_service_url, subpath)
