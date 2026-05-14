import os
from flask import Flask

from app.config import config_by_name
from app.extensions import csrf, db, login_manager


def create_app(config_name: str = "dev") -> Flask:
    app = Flask(__name__)
    config_obj = config_by_name[config_name]
    app.config.from_object(config_obj)
    
    if hasattr(config_obj, "init_app"):
        config_obj.init_app(app)

    # Ensure upload directory exists
    upload_folder = app.config.get("UPLOAD_FOLDER")
    if upload_folder and not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    with app.app_context():
        from app.models import User  # noqa: F401
        
        @login_manager.user_loader
        def load_user(user_id: str) -> User | None:
            return db.session.get(User, int(user_id))

        # Blueprints will be registered here (Step 3.3)
        from app.blueprints import api_bp, auth_bp, dashboard_bp
        app.register_blueprint(auth_bp)
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(api_bp)

    return app
