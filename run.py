import os

from app import create_app
from app.extensions import db

# Determine config based on environment variable, default to dev
config_name = os.getenv("FLASK_ENV", "dev")
app = create_app(config_name)

if __name__ == "__main__":
    with app.app_context():
        # Create all tables (in real life use Alembic for migrations)
        db.create_all()

    from update_db import update_db_schema
    update_db_schema(app)

    app.run(host="0.0.0.0", port=5000)
