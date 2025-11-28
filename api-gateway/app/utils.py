# api-gateway/app/utils.py
from flask_jwt_extended import get_jwt_identity


def get_current_identity():
    """Retorna o payload do JWT ou {}."""
    return get_jwt_identity() or {}
