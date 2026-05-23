#!/bin/bash
set -e

if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

export FLASK_ENV=${FLASK_ENV:-prod}

if [ -z "$SECRET_KEY" ]; then
    echo "ВНИМАНИЕ: SECRET_KEY не задан! Сессии пользователей будут нестабильными."
fi

python init_db.py

exec gunicorn \
  --workers "${WEB_CONCURRENCY:-2}" \
  --bind "0.0.0.0:${PORT:-10000}" \
  --access-logfile - \
  "run:app"