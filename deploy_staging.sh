#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE=".env"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-motogestor-staging}"
SERVICES_WITH_MIGRATIONS=(users-service management-service financial-service teamcrm-service)
GHCR_USERNAME=${GHCR_USERNAME:-}
GHCR_TOKEN=${GHCR_TOKEN:-}
USE_LOCAL_BUILD=${USE_LOCAL_BUILD:-0}  # quando 1, usa docker-compose.yml e builda localmente (fallback se GHCR negar acesso)

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

# Quando o GHCR está indisponível ou privado, permitir fallback para build local usando docker-compose.yml
if [[ "${USE_LOCAL_BUILD}" == "1" ]]; then
  echo "[deploy] USE_LOCAL_BUILD=1 → usando docker-compose.yml e build local (sem GHCR)."
  COMPOSE_FILE="docker-compose.yml"
  compose_cmd=(docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" -p "${PROJECT_NAME}")
fi

if [[ "${USE_LOCAL_BUILD}" != "1" ]]; then
  if [[ -n "${GHCR_USERNAME}" && -n "${GHCR_TOKEN}" ]]; then
    echo "[deploy] Autenticando no GHCR como ${GHCR_USERNAME}..."
    echo "${GHCR_TOKEN}" | docker login ghcr.io -u "${GHCR_USERNAME}" --password-stdin
  else
    echo "[deploy] GHCR_USERNAME/GHCR_TOKEN não definidos; tentando pull anônimo (garanta permissão pública ou configure o login)." >&2
  fi

  echo "[deploy] Pulling imagens ${IMAGE_TAG:-0.0.1} do GHCR..."
  "${compose_cmd[@]}" pull postgres redis users-service management-service financial-service teamcrm-service ai-service api-gateway
else
  echo "[deploy] Pulando pull do GHCR (USE_LOCAL_BUILD=1). Construindo localmente quando necessário..."
  "${compose_cmd[@]}" build
fi

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
