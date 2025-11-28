import time

from flask import Flask, jsonify
from flask_jwt_extended import JWTManager, verify_jwt_in_request
from sqlalchemy.exc import OperationalError

from .config import load_config
from .errors import register_error_handlers
from .logging_setup import setup_logging
from .models import db
from .tenant import set_current_tenant_from_jwt


def create_app() -> Flask:
    setup_logging()
    cfg = load_config()

    app = Flask(__name__)

    app.config["ENV"] = cfg.app_env
    app.config["JWT_SECRET_KEY"] = cfg.jwt_secret_key
    app.config["SQLALCHEMY_DATABASE_URI"] = cfg.database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    jwt = JWTManager(app)  # noqa: F841

    register_error_handlers(app)

    @app.before_request
    def inject_tenant_context():
        verify_jwt_in_request(optional=True)  # carrega claims se existirem
        set_current_tenant_from_jwt()

    # Blueprints
    from .routes_auth import bp as auth_bp
    from .routes_seed import bp as seed_bp
    from .routes_users import bp as users_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(users_bp, url_prefix="/users")
    app.register_blueprint(seed_bp, url_prefix="/users")

    @app.route("/health")
    def health():
        try:
            db.session.execute("SELECT 1")
            return {"status": "ok", "service": "users-service"}, 200
        except OperationalError:
            return jsonify({"status": "degraded", "service": "users-service"}), 503

    # DEV only: tenta criar tabelas com alguns retries
    if app.config["ENV"] == "development":
        with app.app_context():
            attempts = 10
            while attempts > 0:
                try:
                    db.create_all()
                    print("Tabelas criadas/validadas com sucesso.")
                    break
                except OperationalError as e:
                    attempts -= 1
                    print(
                        f"[users-service] Banco não pronto, tentando de novo... ({attempts})"
                    )
                    print(str(e))
                    time.sleep(3)

    return app
