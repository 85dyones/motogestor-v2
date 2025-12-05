#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE="${ENV_FILE:-.env.e2e}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-motogestor-e2e}"
SERVICES_WITH_MIGRATIONS=(users-service management-service financial-service teamcrm-service)
GATEWAY_PORT=${GATEWAY_PORT:-80}

if [[ ! -f "${ENV_FILE}" ]]; then
  cat > "${ENV_FILE}" <<'EOF'
POSTGRES_USER=motogestor
POSTGRES_PASSWORD=motogestor
POSTGRES_DB=motogestor_e2e
JWT_SECRET_KEY=dev-secret-key
APP_ENV=test
LOG_LEVEL=INFO
EOF
fi

compose_cmd=(docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" -p "${PROJECT_NAME}")

cleanup() {
  echo "[e2e] Cleaning up compose stack..."
  "${compose_cmd[@]}" down -v || true
}
trap cleanup EXIT

export COMPOSE_PROJECT_NAME="${PROJECT_NAME}"

echo "[e2e] Pulling GHCR images..."
"${compose_cmd[@]}" pull

echo "[e2e] Starting database and redis..."
"${compose_cmd[@]}" up -d postgres redis

echo "[e2e] Waiting for postgres to be ready..."
until "${compose_cmd[@]}" exec -T postgres pg_isready -U "${POSTGRES_USER:-motogestor}" >/dev/null 2>&1; do
  sleep 2
done

echo "[e2e] Applying migrations..."
for service in "${SERVICES_WITH_MIGRATIONS[@]}"; do
  "${compose_cmd[@]}" run --rm "$service" alembic upgrade head
done

echo "[e2e] Starting the full stack..."
"${compose_cmd[@]}" up -d

GATEWAY_BASE_URL=${GATEWAY_BASE_URL:-"http://localhost:${GATEWAY_PORT}"}

echo "[e2e] Waiting for api-gateway at ${GATEWAY_BASE_URL}/health..."
for _ in {1..30}; do
  if curl -fsS "${GATEWAY_BASE_URL}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "[e2e] Running pytest end-to-end suite..."
GATEWAY_BASE_URL="$GATEWAY_BASE_URL" pytest -c tests/e2e/pytest.ini tests/e2e

echo "[e2e] Tests completed. Stack will be torn down by trap."
