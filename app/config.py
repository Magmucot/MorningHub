import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Base configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-replace-in-prod")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = BASE_DIR / "app" / "static" / "uploads"
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max file size


class DevConfig(Config):
    """Development configuration."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'morninghub_dev.db'}")


class ProdConfig(Config):
    """Production configuration."""

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    @classmethod
    def init_app(cls, app):
        if not cls.SQLALCHEMY_DATABASE_URI:
            raise ValueError("DATABASE_URL environment variable is required in production.")


config_by_name = dict(dev=DevConfig, prod=ProdConfig)
