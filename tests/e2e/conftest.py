import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Dict, Tuple

import httpx
import pytest


def _bootstrap_stack_if_requested() -> bool:
    if os.getenv("AUTO_START_STACK") != "1":
        return False

    script_path = Path(__file__).resolve().parents[1] / "start_stack.sh"
    env = os.environ.copy()
    env.setdefault("LEAVE_UP", "1")
    env.setdefault("COMPOSE_FILE", env.get("COMPOSE_FILE", "docker-compose.test.yml"))
    env.setdefault("ENV_FILE", env.get("ENV_FILE", ".env.test"))
    env.setdefault("GATEWAY_PORT", env.get("GATEWAY_PORT", "5000"))
    try:
        subprocess.run([str(script_path)], env=env, check=True)
    except FileNotFoundError:
        pytest.skip("docker not installed; cannot bootstrap e2e stack")
    except subprocess.CalledProcessError as exc:
        pytest.skip(f"failed to bootstrap stack: {exc}")
    return True


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.getenv("GATEWAY_BASE_URL", "http://localhost:5000").rstrip("/")


@pytest.fixture(scope="session")
def client(base_url: str):
    started = False
    client = httpx.Client(base_url=base_url, timeout=30.0)
    for _ in range(30):
        try:
            resp = client.get("/health")
            if resp.status_code < 500:
                break
        except Exception:
            if not started:
                started = _bootstrap_stack_if_requested()
                if started:
                    continue
            time.sleep(2)
            continue
    else:
        pytest.skip("api-gateway not reachable for e2e tests")

    try:
        yield client
    finally:
        client.close()
        if started:
            teardown_env = os.environ.copy()
            teardown_env.update({"TEARDOWN": "1", "LEAVE_UP": "0"})
            script_path = Path(__file__).resolve().parents[1] / "start_stack.sh"
            subprocess.run([str(script_path)], env=teardown_env, check=False)


@pytest.fixture(scope="session")
def seed_user(client: httpx.Client) -> Tuple[Dict[str, str], str]:
    email = f"e2e-{uuid.uuid4().hex[:8]}@example.com"
    password = "Password123!"
    tenant_name = f"tenant-{uuid.uuid4().hex[:6]}"
    resp = client.post(
        "/auth/register",
        json={
            "name": "E2E Owner",
            "email": email,
            "password": password,
            "tenant_name": tenant_name,
        },
    )
    assert resp.status_code in (200, 201), resp.text
    payload = resp.json()
    access_token = payload["access_token"]
    tenant_id = payload["user"]["tenant_id"]
    headers = {"Authorization": f"Bearer {access_token}"}
    return headers, tenant_id
