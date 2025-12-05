# management-service/app/__init__.py
import os

from flask import Flask
from flask_jwt_extended import JWTManager

from .models import db
from .observability import register_observability
from .tenant_guard import inject_current_tenant_from_token


def create_app():
    app = Flask(__name__)
    register_observability(app, "management-service")

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

    @app.before_request
    def inject_tenant():
        inject_current_tenant_from_token(optional=True)

    from .routes_customers import bp as customers_bp
    from .routes_motos import bp as motos_bp
    from .routes_os import bp as os_bp
    from .routes_parts import bp as parts_bp

    app.register_blueprint(customers_bp, url_prefix="/customers")
    app.register_blueprint(motos_bp, url_prefix="/motos")
    app.register_blueprint(parts_bp, url_prefix="/parts")
    app.register_blueprint(os_bp, url_prefix="/os")

    @app.route("/health")
    def health():
        return {"status": "ok", "service": "management-service"}, 200

    with app.app_context():
        db.create_all()

    return app
