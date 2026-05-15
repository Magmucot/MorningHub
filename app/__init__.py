import os
from flask import Flask
from pathlib import Path
from app.config import config_by_name
from app.extensions import csrf, db, login_manager


def create_app(config_name: str = "dev") -> Flask:
    app = Flask(__name__)
    config_obj = config_by_name[config_name]
    app.config.from_object(config_obj)

    if hasattr(config_obj, "init_app"):
        config_obj.init_app(app)

    # Поддержка пользовательского имени переменной БД для Flask-SQLAlchemy
    if "SQLALCHEMY_DB_URI" in app.config:
        app.config["SQLALCHEMY_DATABASE_URI"] = app.config["SQLALCHEMY_DB_URI"]
    upload_folder = app.config.get("UPLOAD_FOLDER")
    if upload_folder and not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_uri.startswith("sqlite:///"):
        db_path = Path(db_uri.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)

    # Расширения
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    with app.app_context():
        from app.models import User

        @login_manager.user_loader
        def load_user(user_id: str) -> User | None:
            return db.session.get(User, int(user_id))

        from app.blueprints import api_bp, auth_bp, dashboard_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(api_bp)

    return app
