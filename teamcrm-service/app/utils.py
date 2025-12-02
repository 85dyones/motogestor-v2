# teamcrm-service/app/utils.py
from flask_jwt_extended import get_jwt_identity, get_jwt


def get_current_identity():
    identity = get_jwt_identity()
    if isinstance(identity, dict):
        return identity
    claims = get_jwt()
    return claims or {}


def get_current_tenant_id():
    identity = get_current_identity()
    return identity.get("tenant_id")


def is_manager_or_owner():
    identity = get_current_identity()
    return identity.get("role") in ("owner", "manager")
