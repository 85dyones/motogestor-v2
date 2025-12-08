#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.test.yml}"
ENV_FILE="${ENV_FILE:-.env.test}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-motogestor-tests}"
SERVICES_WITH_MIGRATIONS=(users-service management-service financial-service teamcrm-service)
LEAVE_UP="${LEAVE_UP:-0}"
TEARDOWN="${TEARDOWN:-0}"
GATEWAY_PORT="${GATEWAY_PORT:-5000}"

compose_cmd=(docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" -p "${PROJECT_NAME}")

if [[ "${TEARDOWN}" == "1" ]]; then
  echo "[stack] Tearing down stack ${PROJECT_NAME}..."
  "${compose_cmd[@]}" down -v || true
  exit 0
fi

cleanup() {
  if [[ "${LEAVE_UP}" != "1" ]]; then
    echo "[stack] Cleaning up stack ${PROJECT_NAME}..."
    "${compose_cmd[@]}" down -v || true
  fi
}
trap cleanup EXIT

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[stack] Env file ${ENV_FILE} not found; creating with defaults..."
  cat > "${ENV_FILE}" <<'EODEFAULT'
POSTGRES_USER=motogestor
POSTGRES_PASSWORD=motogestor
POSTGRES_DB=motogestor_test
POSTGRES_HOST=postgres
JWT_SECRET_KEY=test-secret
DATABASE_URL=postgresql+psycopg2://motogestor:motogestor@postgres:5432/motogestor_test
LOG_LEVEL=INFO
APP_ENV=test
EODEFAULT
fi

export COMPOSE_PROJECT_NAME="${PROJECT_NAME}"

echo "[stack] Building images and pulling base services..."
"${compose_cmd[@]}" up -d --build postgres redis

echo "[stack] Waiting for postgres health..."
until "${compose_cmd[@]}" exec -T postgres pg_isready -U "${POSTGRES_USER:-motogestor}" >/dev/null 2>&1; do
  sleep 2
done

echo "[stack] Running migrations..."
for service in "${SERVICES_WITH_MIGRATIONS[@]}"; do
  "${compose_cmd[@]}" run --rm "$service" alembic upgrade head
done

echo "[stack] Starting remaining services..."
"${compose_cmd[@]}" up -d --build

GATEWAY_BASE_URL=${GATEWAY_BASE_URL:-"http://localhost:${GATEWAY_PORT}"}

echo "[stack] Waiting for api-gateway at ${GATEWAY_BASE_URL}/health..."
for _ in {1..30}; do
  if curl -fsS "${GATEWAY_BASE_URL}/health" >/dev/null 2>&1; then
    echo "[stack] api-gateway is healthy."
    break
  fi
  sleep 2
done

if [[ "${LEAVE_UP}" == "1" ]]; then
  trap - EXIT
  exit 0
fi

echo "[stack] Stack ready; tailing logs (Ctrl+C to stop)..."
"${compose_cmd[@]}" logs -f
