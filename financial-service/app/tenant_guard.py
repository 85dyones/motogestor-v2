"""Tenant enforcement helpers for Flask routes."""

from __future__ import annotations

from functools import wraps
from typing import Iterable, Optional

from flask import g, jsonify, request
from flask_jwt_extended import get_jwt, verify_jwt_in_request

from .models import db

TENANT_CLAIM = "tenant_id"


def _extract_request_tenant(
    path_key: str = "tenant_id", body_keys: Iterable[str] = ("tenant_id",)
) -> Optional[int]:
    if request.view_args and path_key in request.view_args:
        try:
            return int(request.view_args[path_key])
        except (TypeError, ValueError):
            return None
    data = request.get_json(silent=True) or {}
    for key in body_keys:
        if key in data:
            try:
                return int(data.get(key))
            except (TypeError, ValueError):
                return None
    return None


def _set_pg_tenant_scope(tenant_id: int) -> None:
    bind = db.session.get_bind()
    if not bind or bind.dialect.name != "postgresql":
        return
    db.session.execute("SET LOCAL app.current_tenant = :tenant_id", {"tenant_id": tenant_id})


def tenant_guard(path_key: str = "tenant_id", body_keys: Iterable[str] = ("tenant_id",)):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt() or {}
            token_tenant = claims.get(TENANT_CLAIM)
            if token_tenant is None:
                return jsonify({"error": "token sem tenant"}), 403

            request_tenant = _extract_request_tenant(path_key, body_keys)
            if request_tenant is None:
                return jsonify({"error": "tenant_id obrigatório"}), 400

            if int(token_tenant) != int(request_tenant):
                return jsonify({"error": "tenant_id não corresponde"}), 403

            g.current_tenant_id = int(token_tenant)
            _set_pg_tenant_scope(int(token_tenant))
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def inject_current_tenant_from_token(optional: bool = True) -> None:
    verify_jwt_in_request(optional=optional, verify_type=False)
    claims = get_jwt() or {}
    tenant_id = claims.get(TENANT_CLAIM)
    if tenant_id is not None:
        g.current_tenant_id = int(tenant_id)
        _set_pg_tenant_scope(int(tenant_id))
    else:
        g.current_tenant_id = None
