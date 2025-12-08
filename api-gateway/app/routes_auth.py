# api-gateway/app/routes_auth.py
from flask import Blueprint

from .config import load_config
cfg = load_config()
from .proxy import forward_request

bp = Blueprint("auth_proxy", __name__)

ALL_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]


@bp.route("/auth", defaults={"path": ""}, methods=ALL_METHODS)
@bp.route("/auth/<path:path>", methods=ALL_METHODS)
def auth_proxy(path: str):
    """
    Encaminha /auth/... para o users-service (/auth/...).
    """
    subpath = f"auth/{path}" if path else "auth"
    return forward_request(cfg.users_service_url, subpath)


@bp.route("/me", methods=["GET"])
def me_proxy():
    """
    Encaminha /me para o users-service (/me).
    """
    return forward_request(cfg.users_service_url, "me")
