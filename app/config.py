import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()


class Config:
    """Базовый конфиг"""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-replace-in-prod"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = BASE_DIR / "app" / "static" / "uploads"
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB


class DevConfig(Config):
    """Разраб сборка"""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DB_URL", f"sqlite:///{BASE_DIR / 'db' / 'morninghub_dev.db'}")


class ProdConfig(Config):
    """Продуктовая сборка"""

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DB_URL")

    @classmethod
    def init_app(cls, app):
        if not cls.SQLALCHEMY_DATABASE_URI:
            raise ValueError("Переменная среды DB_URL требуется в рабочей среде.")


config_by_name = {
    "dev": DevConfig,
    "development": DevConfig,
    "prod": ProdConfig,
    "production": ProdConfig,
}
