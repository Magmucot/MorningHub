#!/bin/bash
# start.sh

# Загружаем переменные из .env, если файл существует
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

if [ -d ".venv" ]; then
    . .venv/bin/activate
fi

export FLASK_ENV=${FLASK_ENV:-prod}

# Проверяем, задан ли SECRET_KEY (через окружение или .env)
if [ -z "$SECRET_KEY" ]; then
    export SECRET_KEY=$(openssl rand -hex 32)
    echo "ВНИМАНИЕ: SECRET_KEY не задан! Сгенерирован случайный ключ."
fi

export DB_URL=${DB_URL:-sqlite:///$(pwd)/db/morninghub_prod.db}
export AI_API_KEY=${AI_API_KEY:-""}

echo "Запуск MorningHub..."
echo "База данных: $DB_URL"

python << EOF
import os
from app.models.widget import WidgetConfig
from app.models.bookmark import Bookmark
from app import create_app
from app.extensions import db

db_url = os.environ["DB_URL"]
app = create_app(os.environ.get("FLASK_ENV", "prod"))
with app.app_context():
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "", 1)
        if not os.path.exists(db_path):
            db.create_all()
    else:
        db.create_all()
EOF

exec gunicorn -w ${WEB_CONCURRENCY:-2} --bind 0.0.0.0:${PORT:-10000} --access-logfile - "run:app"