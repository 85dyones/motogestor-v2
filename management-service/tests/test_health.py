import pytest


def test_health_endpoint():
    import os
    from app import create_app

    # Ensure test DB uses sqlite in-memory so create_app doesn't attempt to connect to postgres
    os.environ.setdefault("APP_ENV", "test")
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

    app = create_app()
    client = app.test_client()

    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("status") == "ok"
    assert data.get("service") == "management-service"
