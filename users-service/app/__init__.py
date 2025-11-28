import os
import time
from flask import Flask
from flask_jwt_extended import JWTManager
from sqlalchemy.exc import OperationalError

from .models import db


def create_app() -> Flask:
    app = Flask(__name__)

    # Ambiente
    app.config["ENV"] = os.getenv("APP_ENV", "development")

    # JWT
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-secret")

    # Config do banco via env
    db_user = os.getenv("POSTGRES_USER", "motogestor")
    db_password = os.getenv("POSTGRES_PASSWORD", "motogestor_pwd")
    db_host = os.getenv("POSTGRES_HOST", "postgres")
    db_name = os.getenv("POSTGRES_DB", "motogestor_dev")

    database_url = os.getenv(
        "DATABASE_URL",
        f"postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}",
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    jwt = JWTManager(app)  # noqa: F841

    # Blueprints
    from .routes_auth import bp as auth_bp
    from .routes_users import bp as users_bp
    from .routes_seed import bp as seed_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(users_bp, url_prefix="/users")
    app.register_blueprint(seed_bp, url_prefix="/users")

    @app.route("/health")
    def health():
        return {
            "status": "ok",
            "service": "users-service",
        }, 200

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
                    print(f"[users-service] Banco não pronto, tentando de novo... ({attempts})")
                    print(str(e))
                    time.sleep(3)

    return app
