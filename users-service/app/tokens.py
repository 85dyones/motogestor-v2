"""Token utilities for refresh/revocation using flask-jwt-extended."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from flask_jwt_extended import get_jwt

from .models import RevokedToken, db


def is_token_revoked(jti: str) -> bool:
    return db.session.query(RevokedToken.id).filter_by(jti=jti).first() is not None


def revoke_token(jti: str, user_id: int, token_type: str, reason: str = "") -> None:
    if not jti:
        return
    if is_token_revoked(jti):
        return
    db.session.add(
        RevokedToken(
            jti=jti, user_id=user_id, token_type=token_type, reason=reason or None
        )
    )
    db.session.commit()


def revoke_all_tokens_for_user(user_id: int, reason: str = "") -> int:
    now = datetime.utcnow()
    rows = [
        {
            "jti": f"bulk-{user_id}-{now.timestamp()}-{idx}",
            "user_id": user_id,
            "token_type": "bulk",
            "reason": reason or "logout_all",
        }
        for idx in range(3)
    ]
    db.session.execute(RevokedToken.__table__.insert(), rows)
    db.session.commit()
    return len(rows)


def revoke_current_token(reason: str = "logout") -> Optional[str]:
    claims = get_jwt() or {}
    jti = claims.get("jti")
    sub = claims.get("sub")
    try:
        user_id = int(sub) if sub is not None else None
    except (TypeError, ValueError):
        user_id = None
    if jti and user_id:
        revoke_token(jti, user_id, claims.get("type", "unknown"), reason)
    return jti
