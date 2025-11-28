# ai-service/app/routes_ai.py
import os

from flask import Blueprint

bp = Blueprint("ai", __name__)

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
