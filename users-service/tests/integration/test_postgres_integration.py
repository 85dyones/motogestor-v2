import os
import time

import pytest

from app import create_app
from app.models import db


@pytest.fixture()
def integration_app(monkeypatch):
    # CI job will provide DATABASE_URL or POSTGRES_* env vars
    monkeypatch.setenv("APP_ENV", "development")

    # allow overriding via env vars (CI sets those). If not set, use sensible defaults
    os.environ.setdefault("POSTGRES_USER", "motogestor")
    os.environ.setdefault("POSTGRES_PASSWORD", "motogestor_pwd")
    os.environ.setdefault("POSTGRES_HOST", "localhost")
    os.environ.setdefault("POSTGRES_DB", "motogestor_integration")

    # build DATABASE_URL if not provided
    if not os.environ.get("DATABASE_URL"):
        os.environ["DATABASE_URL"] = (
            f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@"
            f"{os.environ['POSTGRES_HOST']}:5432/{os.environ['POSTGRES_DB']}"
        )

    # Retry waiting for the DB to be ready (Postgres in CI may take a moment)
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            application = create_app()
            with application.app_context():
                db.create_all()
            return application
        except Exception as e:  # OperationalError / connection refused etc.
            if attempt < max_attempts - 1:
                time.sleep(2)
                continue
            raise


@pytest.fixture()
def client(integration_app):
    return integration_app.test_client()


def test_seed_and_login_against_postgres(client):
    # Seed demo user (POST /auth/seed-demo)
    resp = client.post("/users/seed-demo")
    assert resp.status_code in (200, 201)

    # Login with the seeded demo credentials
    login = client.post("/auth/login", json={"email": "demo@motogestor.com", "password": "demo123"})
    assert login.status_code == 200
    data = login.get_json()
    assert "access_token" in data
