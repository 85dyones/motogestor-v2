#!/usr/bin/env bash
set -euo pipefail

# Quick preflight to validate GHCR access for all production images and a given tag.
# Usage: IMAGE_TAG=latest GHCR_USERNAME=... GHCR_TOKEN=... ./scripts/check-ghcr-images.sh

IMAGE_TAG="${IMAGE_TAG:-latest}"
GHCR_USERNAME="${GHCR_USERNAME:-}"
GHCR_TOKEN="${GHCR_TOKEN:-}"

IMAGES=(
  "ghcr.io/85dyones/motogestor-v2-gateway"
  "ghcr.io/85dyones/motogestor-v2-users"
  "ghcr.io/85dyones/motogestor-v2-management"
  "ghcr.io/85dyones/motogestor-v2-financial"
  "ghcr.io/85dyones/motogestor-v2-teamcrm"
  "ghcr.io/85dyones/motogestor-v2-ai"
)

if [[ -n "$GHCR_USERNAME" && -n "$GHCR_TOKEN" ]]; then
  echo "[ghcr-check] Authenticating to ghcr.io as $GHCR_USERNAME..."
  echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USERNAME" --password-stdin >/dev/null
else
  echo "[ghcr-check] GHCR_USERNAME/GHCR_TOKEN not set; attempting anonymous pulls (images must be public)." >&2
fi

for image in "${IMAGES[@]}"; do
  ref="${image}:${IMAGE_TAG}"
  echo "[ghcr-check] Pulling ${ref}..."
  if ! docker pull "${ref}"; then
    echo "[ghcr-check] ERROR: Failed to pull ${ref}. Check tag existence and GHCR permissions." >&2
    exit 1
  fi
done

echo "[ghcr-check] All images pulled successfully."
