# api-gateway/app/utils.py
from flask_jwt_extended import get_jwt_identity, get_jwt


def get_current_identity():
    """Retorna o payload do JWT ou {} (faz fallback para claims se identity não for dict)."""
    identity = get_jwt_identity()
    if isinstance(identity, dict):
        return identity
    claims = get_jwt()
    return claims or {}
