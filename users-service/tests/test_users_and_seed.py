from __future__ import annotations

from .factories import create_tenant, create_user


def test_list_users_scoped(client):
    tenant_a = create_tenant(name="Alpha")
    tenant_b = create_tenant(name="Beta")
    user_a = create_user(tenant_a, password="secret123")
    create_user(tenant_a, password="secret123")
    create_user(tenant_b, password="secret123")

    login = client.post(
        "/auth/login",
        json={"email": user_a.email, "password": "secret123"},
    ).get_json()
    token = login["access_token"]

    resp = client.get("/users/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    users = resp.get_json()
    assert len(users) == 2
    assert all(u["tenant_id"] == tenant_a.id for u in users)


def test_seed_demo_idempotent(client):
    first = client.post("/users/seed-demo")
    assert first.status_code == 201
    second = client.post("/users/seed-demo")
    assert second.status_code == 201
    body = second.get_json()
    assert body["user"]["email"] == "demo@motogestor.com"
