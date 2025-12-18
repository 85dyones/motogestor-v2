import uuid
from datetime import date

import pytest


@pytest.mark.e2e
def test_full_flow(client, seed_user):
    headers, tenant_id = seed_user

    # Create customer
    customer_resp = client.post(
        "/management/customers",
        headers=headers,
        json={"name": "Cliente E2E", "phone": "11999990000"},
    )
    assert customer_resp.status_code == 201, customer_resp.text
    customer_id = customer_resp.json()["id"]

    # Create motorcycle
    moto_resp = client.post(
        "/management/motos",
        headers=headers,
        json={
            "customer_id": customer_id,
            "brand": "Honda",
            "model": "E2E",
            "plate": f"E2E-{uuid.uuid4().hex[:4].upper()}",
            "year": 2023,
            "km_current": 500,
        },
    )
    assert moto_resp.status_code == 201, moto_resp.text
    moto_id = moto_resp.json()["id"]

    # Open service order
    os_resp = client.post(
        "/management/os",
        headers=headers,
        json={
            "tenant_id": tenant_id,
            "customer_id": customer_id,
            "motorcycle_id": moto_id,
            "description": "Troca de óleo",
        },
    )
    assert os_resp.status_code == 201, os_resp.text
    os_id = os_resp.json()["id"]

    # Register financial receivable from OS
    rec_resp = client.post(
        "/financial/receivables/from-os",
        headers=headers,
        json={
            "service_order_id": os_id,
            "customer_name": "Cliente E2E",
            "amount": 250.0,
            "due_date": date.today().isoformat(),
            "description": "OS automatizada",
        },
    )
    assert rec_resp.status_code in (201, 403), rec_resp.text

    # Fetch dashboard summary (teamcrm)
    dash_resp = client.get("/teamcrm/dashboard/summary", headers=headers)
    assert dash_resp.status_code == 200, dash_resp.text
    summary = dash_resp.json()
    assert "tasks" in summary and "interactions" in summary
