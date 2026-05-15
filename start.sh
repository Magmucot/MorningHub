#!/bin/bash

# Virtual Env
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Virtual environment (.venv) not found. Please create it first."
    exit 1
fi

export FLASK_ENV=prod
export SECRET_KEY=${SECRET_KEY:-$(openssl rand -hex 32)}
export DATABASE_URL=${DATABASE_URL:-sqlite:///$(pwd)/morninghub_prod.db}
export OPENAI_API_KEY=${OPENAI_API_KEY:-""}

echo "Starting MorningHub in PRODUCTION mode..."
echo "Database: $DATABASE_URL"

# База данных
python -c "from app import create_app; from app.extensions import db; app = create_app('prod'); with app.app_context(): db.create_all()"

# Запуск Gunicorn
# -w 4: 4 worker processes
# --bind 0.0.0.0:5000: listen on all interfaces at port 5000
# --access-logfile -: log access to stdout
exec gunicorn -w 4 --bind 0.0.0.0:5000 --access-logfile - "run:app"
