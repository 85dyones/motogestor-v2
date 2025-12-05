# teamcrm-service/app/__init__.py
import os

from flask import Flask
from flask_jwt_extended import JWTManager

from .models import db
from .observability import register_observability
from .tenant_guard import inject_current_tenant_from_token


def create_app():
    app = Flask(__name__)
    register_observability(app, "teamcrm-service")

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

    from .routes_dashboard import bp as dash_bp
    from .routes_interactions import bp as inter_bp
    from .routes_staff import bp as staff_bp
    from .routes_tasks import bp as tasks_bp

    app.register_blueprint(staff_bp, url_prefix="/staff")
    app.register_blueprint(tasks_bp, url_prefix="/tasks")
    app.register_blueprint(inter_bp, url_prefix="/interactions")
    app.register_blueprint(dash_bp, url_prefix="/dashboard")

    @app.route("/health")
    def health():
        return {"status": "ok", "service": "teamcrm-service"}, 200

    with app.app_context():
        db.create_all()

    return app
