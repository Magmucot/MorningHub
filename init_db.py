# init_db.py

import os
from app import create_app
from app.extensions import db

# Явный импорт моделей для регистрации метаданных
from app.models.user import User
from app.models.widget import WidgetConfig
from app.models.bookmark import Bookmark

fl_env = os.getenv("FLASK_ENV", "prod")
app = create_app(fl_env)

with app.app_context():
    db.create_all()

from update_db import update_db_schema
update_db_schema(app)
