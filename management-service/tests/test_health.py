import pytest


def test_health_endpoint():
    from app import create_app

    app = create_app()
    client = app.test_client()

    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("status") == "ok"
    assert data.get("service") == "management-service"
