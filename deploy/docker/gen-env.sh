#!/usr/bin/env bash
# Generate server .env from .env.docker.example with unique SECRET_KEY + DB_PASSWORD.
# Usage (on Droplet or Mac): bash deploy/docker/gen-env.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

SRC="$ROOT/.env.docker.example"
DST="$ROOT/.env"

if [ ! -f "$SRC" ]; then
  echo "FATAL: missing $SRC"
  exit 1
fi
if [ -f "$DST" ]; then
  echo "FATAL: $DST already exists — refuse to overwrite"
  exit 1
fi

SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')"
DB_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"

sed \
  -e "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" \
  -e "s|^DB_PASSWORD=.*|DB_PASSWORD=${DB_PASSWORD}|" \
  "$SRC" > "$DST"

chmod 600 "$DST"
echo "==> wrote $DST (SECRET_KEY + DB_PASSWORD generated)"
echo "==> verify:"
grep -E '^(ALLOWED_HOSTS|CSRF_TRUSTED_ORIGINS|SESSION_COOKIE_SECURE|SECURE_SSL_REDIRECT)=' "$DST"
if grep -E '^(ALLOWED_HOSTS|CSRF_TRUSTED_ORIGINS)=.*DROPLET_IP' "$DST"; then
  echo "FATAL: DROPLET_IP token in ALLOWED_HOSTS/CSRF_TRUSTED_ORIGINS"
  exit 1
fi
if ! grep -q '161.35.65.129' "$DST"; then
  echo "FATAL: expected droplet IP 161.35.65.129 missing from .env"
  exit 1
fi
