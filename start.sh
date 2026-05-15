#!/bin/bash
# start.sh

# Virtual Env
if [ -d ".venv" ]; then
    . .venv/bin/activate
else
    echo "Virtual environment (.venv) не найдены. Создайте их сначала"
    exit 1
fi

export FLASK_ENV=prod
export SECRET_KEY=${SECRET_KEY:-$(openssl rand -hex 32)}
export DB_URL=${DB_URL:-sqlite:///$(pwd)/db/morninghub_prod.db}
export AI_API_KEY=${AI_API_KEY:-""}

echo "Запуск MorningHub в PROD моде..."


# База данных
echo "База данных: $DB_URL"
python << EOF
from app import create_app
from app.extensions import db
app = create_app('prod')
with app.app_context():
    db.create_all()
EOF

# Запуск Gunicorn
# -w 4: 4 worker processes
# --bind 0.0.0.0:5000: listen on all interfaces at port 5000
# --access-logfile -: log access to stdout
exec gunicorn -w 4 --bind 0.0.0.0:5000 --access-logfile - "run:app"
