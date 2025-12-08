# financial-service/app/utils.py
from flask_jwt_extended import get_jwt_identity, get_jwt


def get_current_identity():
    identity = get_jwt_identity()
    # prefer identity if it's a mapping (tests sometimes set identity as a string)
    if isinstance(identity, dict):
        return identity
    # fallback to JWT claims (additional_claims)
    claims = get_jwt()
    return claims or {}


def get_current_tenant_id():
    identity = get_current_identity()
    return identity.get("tenant_id")


def is_manager_or_owner():
    identity = get_current_identity()
    return identity.get("role") in ("owner", "manager")
