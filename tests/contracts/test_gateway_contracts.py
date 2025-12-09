import uuid
from datetime import date

import pytest


@pytest.mark.contract
def test_auth_login_and_me_flow(client, registered_user):
    login_resp = client.post(
        "/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    assert login_resp.status_code == 200
    payload = login_resp.json()
    assert {"access_token", "refresh_token", "user"}.issubset(payload.keys())

    access_token = payload["access_token"]
    me_resp = client.get("/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_resp.status_code == 200
    me_json = me_resp.json()
    for key in ["id", "email", "name", "tenant_id"]:
        assert key in me_json


@pytest.mark.contract
def test_auth_error_shape_is_preserved(client):
    bad_login = client.post(
        "/auth/login", json={"email": "ghost@example.com", "password": "wrong"}
    )
    assert bad_login.status_code in (401, 422)
    body = bad_login.json()
    assert "error" in body
    assert {"message", "code"}.issubset(body["error"].keys())


@pytest.mark.contract
def test_management_os_pipeline(client, auth_headers, registered_user):
    # Create customer
    cust_resp = client.post(
        "/management/customers",
        headers=auth_headers,
        json={"name": "Cliente Contrato"},
    )
    assert cust_resp.status_code == 201
    customer_id = cust_resp.json()["id"]

    # Create motorcycle for the customer
    moto_resp = client.post(
        "/management/motos",
        headers=auth_headers,
        json={
            "customer_id": customer_id,
            "brand": "Honda",
            "model": "CG",
            "plate": f"TEST-{uuid.uuid4().hex[:4].upper()}",
            "year": 2022,
            "km_current": 1000,
        },
    )
    assert moto_resp.status_code == 201
    moto_id = moto_resp.json()["id"]

    # Create service order with tenant guard
    os_resp = client.post(
        "/management/os",
        headers=auth_headers,
        json={
            "tenant_id": registered_user["tenant_id"],
            "customer_id": customer_id,
            "motorcycle_id": moto_id,
            "description": "Revisão completa",
        },
    )
    assert os_resp.status_code == 201
    os_body = os_resp.json()
    assert {"id", "status"}.issubset(os_body)

    # Update status with tenant guard mismatch to ensure 403
    forbidden = client.patch(
        f"/management/os/{os_body['id']}/status",
        headers=auth_headers,
        json={"tenant_id": registered_user["tenant_id"] + 999, "status": "COMPLETED"},
    )
    assert forbidden.status_code in (400, 403)


@pytest.mark.contract
def test_financial_receivable_contract(client, auth_headers, registered_user):
    # Create an ad-hoc receivable
    create_resp = client.post(
        "/financial/receivables",
        headers=auth_headers,
        json={
            "tenant_id": registered_user["tenant_id"],
            "description": "Contrato teste",
            "amount": 150.75,
            "due_date": date.today().isoformat(),
        },
    )
    assert create_resp.status_code in (201, 400), create_resp.text
    rec_id = create_resp.json().get("id") if create_resp.status_code == 201 else None

    list_resp = client.get("/financial/receivables", headers=auth_headers)
    assert list_resp.status_code == 200
    payload = list_resp.json()
    assert isinstance(payload, list)
    if payload:
        sample = payload[0]
        assert {"id", "amount", "status"}.issubset(sample.keys())

    if rec_id:
        # Trigger validation error with missing tenant guard to ensure error shape
        invalid = client.patch(
            f"/financial/receivables/{rec_id}",
            headers=auth_headers,
            json={"tenant_id": registered_user["tenant_id"] + 123, "status": "PAID"},
        )
        assert invalid.status_code in (400, 403)
        body = invalid.json()
        if isinstance(body, dict) and "error" in body:
            assert {"message", "code"}.issubset(body["error"].keys())
