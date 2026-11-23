#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if command -v systemctl >/dev/null 2>&1; then
  systemctl stop nginx 2>/dev/null || true
  systemctl stop gunicorn 2>/dev/null || true
fi

docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
