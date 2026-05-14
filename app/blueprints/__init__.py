from app.blueprints.auth import bp as auth_bp
from app.blueprints.dashboard import bp as dashboard_bp
from app.blueprints.api import bp as api_bp

__all__ = ["auth_bp", "dashboard_bp", "api_bp"]
