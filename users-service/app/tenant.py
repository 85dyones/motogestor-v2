"""Tenant scoping utilities to guarantee multi-tenant isolation at query level."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Type

from flask import g
from flask_jwt_extended import get_jwt

from .errors import ForbiddenError
from .models import db

TENANT_ID_CLAIM = "tenant_id"
PLAN_CLAIM = "plan"


def set_current_tenant_from_jwt() -> None:
    try:
        claims = get_jwt()
    except Exception:
        g.current_tenant_id = None
        g.current_plan = None
        return
    g.current_tenant_id = claims.get(TENANT_ID_CLAIM)
    g.current_plan = claims.get(PLAN_CLAIM)


def current_tenant_id() -> int | None:
    return getattr(g, "current_tenant_id", None)


def ensure_tenant_scope() -> int:
    tenant_id = current_tenant_id()
    if tenant_id is None:
        raise ForbiddenError("Contexto de tenant ausente ou inválido.")
    return tenant_id


def tenant_query(model: Type[db.Model]):
    tenant_id = ensure_tenant_scope()
    if hasattr(model, "tenant_id"):
        return model.query.filter_by(tenant_id=tenant_id)
    return model.query


@contextmanager
def enforce_tenant_scope() -> Generator[int, None, None]:
    tenant_id = ensure_tenant_scope()
    yield tenant_id
