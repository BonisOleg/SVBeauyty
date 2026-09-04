#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.prod.yml)
SERVICES=(db web nginx)

if ls /etc/letsencrypt/live/*/fullchain.pem >/dev/null 2>&1; then
  COMPOSE+=(-f docker-compose.ssl.yml)
  echo "==> SSL overlay enabled"
fi

free_host_ports() {
  if command -v systemctl >/dev/null 2>&1; then
    systemctl stop nginx 2>/dev/null || true
    systemctl disable nginx 2>/dev/null || true
    systemctl stop gunicorn 2>/dev/null || true
  fi
}

web_healthz_ok() {
  "${COMPOSE[@]}" exec -T web python -c \
    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz/', timeout=5)" \
    >/dev/null 2>&1
}

free_host_ports

echo "==> stop nginx (уникнути 502 під час рестарту web)"
"${COMPOSE[@]}" stop nginx 2>/dev/null || true

echo "==> build + up db web"
"${COMPOSE[@]}" up -d --build --remove-orphans db web || true

echo "==> wait web /healthz/ (gunicorn)"
ok=0
for _ in $(seq 1 60); do
  if web_healthz_ok; then
    ok=1
    break
  fi
  sleep 3
done

if [ "$ok" -ne 1 ]; then
  echo "WARN: web /healthz/ not ready — logs:"
  "${COMPOSE[@]}" logs --tail=40 web db
  exit 1
fi

echo "==> start nginx (web уже healthy)"
"${COMPOSE[@]}" up -d --remove-orphans nginx || true

echo "==> inventory"
missing=0
for svc in "${SERVICES[@]}"; do
  # Compose v2: "running"; Compose v5: "Up" — не покладатись лише на running.
  if "${COMPOSE[@]}" ps "$svc" 2>/dev/null | grep -Eiq 'running|up '; then
    echo "OK: $svc"
  else
    echo "MISSING: $svc (перевір compose ps + curl /healthz/)"
    missing=1
  fi
done

echo "==> web healthz OK"
if [ "$missing" -ne 0 ]; then
  exit 1
fi
