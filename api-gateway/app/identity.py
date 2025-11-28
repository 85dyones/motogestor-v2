"""Shared identity/claim helpers for propagating tenant context between services."""
from __future__ import annotations

from typing import Any, Dict

TENANT_ID_CLAIM = "tenant_id"
PLAN_CLAIM = "plan"
TENANT_NAME_CLAIM = "tenant_name"


def extract_tenant_context(identity: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize tenant-related fields from a JWT identity payload."""
    if not identity:
        return {}
    return {
        "tenant_id": identity.get(TENANT_ID_CLAIM),
        "tenant_name": identity.get(TENANT_NAME_CLAIM),
        "plan": (identity.get(PLAN_CLAIM) or "BASIC").upper(),
    }
