"""Helpers for tenant-aware JWT claims shared across services."""

from __future__ import annotations

from typing import Any, Dict

from flask_jwt_extended import create_access_token

TENANT_ID_CLAIM = "tenant_id"
PLAN_CLAIM = "plan"
TENANT_NAME_CLAIM = "tenant_name"


def build_token(
    identity: int, tenant_id: int, plan: str, tenant_name: str | None = None
) -> str:
    claims = {
        TENANT_ID_CLAIM: tenant_id,
        PLAN_CLAIM: plan or "BASIC",
    }
    if tenant_name:
        claims[TENANT_NAME_CLAIM] = tenant_name
    # PyJWT requires ``sub`` (identity) to be a string for validation to pass.
    return create_access_token(identity=str(identity), additional_claims=claims)


def to_dict(identity: Dict[str, Any]) -> Dict[str, Any]:
    if not identity:
        return {}
    return {
        "tenant_id": identity.get(TENANT_ID_CLAIM),
        "plan": (identity.get(PLAN_CLAIM) or "BASIC").upper(),
        "tenant_name": identity.get(TENANT_NAME_CLAIM),
    }
