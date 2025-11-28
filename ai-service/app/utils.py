# ai-service/app/utils.py
import json
import os
from typing import Optional

from flask_jwt_extended import get_jwt_identity
from openai import OpenAI

from .models import db, AiRequestLog


def get_current_identity():
    return get_jwt_identity() or {}


def get_current_tenant_id():
    identity = get_current_identity()
    return identity.get("tenant_id")


def is_manager_or_owner():
    identity = get_current_identity()
    return identity.get("role") in ("owner", "manager")


def get_openai_client() -> Optional[OpenAI]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def log_ai_request(
    tenant_id: int,
    request_type: str,
    input_data: dict,
    output_data: dict | None,
    success: bool,
    error_message: str | None = None,
):
    try:
        log = AiRequestLog(
            tenant_id=tenant_id,
            request_type=request_type,
            input_payload=json.dumps(input_data, ensure_ascii=False),
            output_payload=(
                json.dumps(output_data, ensure_ascii=False) if output_data else None
            ),
            success=success,
            error_message=error_message,
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        # log silencioso: não vamos quebrar a requisição se o log falhar
        db.session.rollback()
