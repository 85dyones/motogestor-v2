#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"
PROJECT_NAME="motogestor-staging"
SERVICES_WITH_MIGRATIONS=(users-service management-service financial-service teamcrm-service)

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[deploy] Arquivo ${ENV_FILE} não encontrado. Crie-o antes do deploy." >&2
  exit 1
fi

# Exporta variáveis do .env para que pg_isready receba POSTGRES_USER e afins
set -a
source "${ENV_FILE}"
set +a

export APP_ENV="${APP_ENV:-staging}"
export COMPOSE_PROJECT_NAME="${PROJECT_NAME}"

compose_cmd=(docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" -p "${PROJECT_NAME}")

echo "[deploy] Pulling imagens 0.0.1 do GHCR..."
"${compose_cmd[@]}" pull postgres redis users-service management-service financial-service teamcrm-service ai-service api-gateway

echo "[deploy] Subindo postgres/redis em background..."
"${compose_cmd[@]}" up -d postgres redis

echo "[deploy] Aguardando Postgres ficar saudável..."
until "${compose_cmd[@]}" exec -T postgres pg_isready -U "${POSTGRES_USER:-motogestor}" >/dev/null 2>&1; do
  sleep 2
  echo "[deploy] Postgres ainda inicializando..."
done

echo "[deploy] Rodando alembic upgrade head nos serviços com banco..."
for service in "${SERVICES_WITH_MIGRATIONS[@]}"; do
  "${compose_cmd[@]}" run --rm "$service" alembic upgrade head
done

echo "[deploy] Subindo todos os serviços em modo staging..."
"${compose_cmd[@]}" up -d

"${compose_cmd[@]}" ps

echo "[deploy] Deploy de staging concluído com sucesso."
