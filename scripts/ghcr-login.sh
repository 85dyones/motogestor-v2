#!/usr/bin/env bash
set -euo pipefail

# Small helper to login to GHCR using GHCR_USERNAME / GHCR_TOKEN.
# Reads an optional .env file so you can run:
#   ./scripts/ghcr-login.sh .env
#
# Exits with a clear error if credentials are missing.

ENV_FILE="${1:-}"

if [[ -n "${ENV_FILE}" ]]; then
  if [[ ! -f "${ENV_FILE}" ]]; then
    echo "[ghcr-login] Env file '${ENV_FILE}' not found." >&2
    exit 1
  fi
  set -a
  source "${ENV_FILE}"
  set +a
fi

GHCR_USERNAME="${GHCR_USERNAME:-}"
GHCR_TOKEN="${GHCR_TOKEN:-}"

if [[ -z "${GHCR_USERNAME}" || -z "${GHCR_TOKEN}" ]]; then
  echo "[ghcr-login] GHCR_USERNAME/GHCR_TOKEN are required to login to ghcr.io." >&2
  exit 1
fi

echo "[ghcr-login] Logging into ghcr.io as ${GHCR_USERNAME}..."
echo "${GHCR_TOKEN}" | docker login ghcr.io -u "${GHCR_USERNAME}" --password-stdin
echo "[ghcr-login] Login successful."
