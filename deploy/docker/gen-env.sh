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
grep -E '^(ALLOWED_HOSTS|CSRF_TRUSTED_ORIGINS|SESSION_COOKIE_SECURE|CSRF_COOKIE_SECURE|SECURE_SSL_REDIRECT|LIQPAY_ENABLED)=' "$DST"
if grep -E '^(ALLOWED_HOSTS|CSRF_TRUSTED_ORIGINS)=.*DROPLET_IP' "$DST"; then
  echo "FATAL: DROPLET_IP token in ALLOWED_HOSTS/CSRF_TRUSTED_ORIGINS"
  exit 1
fi
if ! grep -q 'svbeauty.com.ua' "$DST"; then
  echo "FATAL: expected domain svbeauty.com.ua missing from .env"
  exit 1
fi
if ! grep -q '^CSRF_TRUSTED_ORIGINS=https://svbeauty.com.ua,https://www.svbeauty.com.ua$' "$DST"; then
  echo "FATAL: CSRF_TRUSTED_ORIGINS must be the https domain"
  exit 1
fi
if ! grep -q '^SESSION_COOKIE_SECURE=True$' "$DST"; then
  echo "FATAL: SESSION_COOKIE_SECURE must be True"
  exit 1
fi
if ! grep -q '^CSRF_COOKIE_SECURE=True$' "$DST"; then
  echo "FATAL: CSRF_COOKIE_SECURE must be True"
  exit 1
fi
if ! grep -q '^LIQPAY_ENABLED=False$' "$DST"; then
  echo "FATAL: LIQPAY_ENABLED must stay False until real FOP keys"
  exit 1
fi
