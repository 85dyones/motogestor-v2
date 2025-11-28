# financial-service/app/__init__.py
import os

from flask import Flask
from flask_jwt_extended import JWTManager

from .models import db


def create_app():
    app = Flask(__name__)

    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-secret")
    app.config["ENV"] = os.getenv("APP_ENV", "development")

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://motogestor:senha123@postgres:5432/motogestor_dev",
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    jwt = JWTManager(app)  # noqa: F841

    from .routes_cashflow import bp as cash_bp
    from .routes_payables import bp as pay_bp
    from .routes_receivables import bp as rec_bp

    app.register_blueprint(rec_bp, url_prefix="/receivables")
    app.register_blueprint(pay_bp, url_prefix="/payables")
    app.register_blueprint(cash_bp, url_prefix="/cashflow")

    @app.route("/health")
    def health():
        return {"status": "ok", "service": "financial-service"}, 200

    with app.app_context():
        db.create_all()

    return app
