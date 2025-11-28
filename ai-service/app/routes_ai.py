# ai-service/app/routes_ai.py
from datetime import datetime, date, timedelta
import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from .models import db
from .utils import (
    get_current_tenant_id,
    get_openai_client,
    log_ai_request,
)

bp = Blueprint("ai", __name__)

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
