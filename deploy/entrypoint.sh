#!/usr/bin/env sh
set -eu

echo "→ migrate"
python manage.py migrate --noinput

echo "→ collectstatic"
python manage.py collectstatic --noinput

echo "→ compilemessages"
python manage.py compilemessages || true

echo "→ gunicorn"
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile - \
  --error-logfile -
