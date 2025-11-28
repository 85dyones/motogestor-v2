# ai-service/app/models.py
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class AiRequestLog(db.Model):
    __tablename__ = "ai_request_logs"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False, index=True)

    request_type = db.Column(
        db.String(50), nullable=False
    )  # whatsapp_message, maintenance_recommendation, os_note, generic_chat
    input_payload = db.Column(db.Text)  # JSON como string
    output_payload = db.Column(db.Text)  # JSON como string
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
