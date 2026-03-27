import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/coletor_dama",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuracoes operacionais iniciais
    APP_NAME = os.getenv("APP_NAME", "Coletor DAMA")
    ITEMS_PER_PAGE = int(os.getenv("ITEMS_PER_PAGE", "20"))

    # Autenticacao para o agent sincronizador (VPS)
    SYNC_API_KEY = os.getenv("SYNC_API_KEY", "")

    # Banco externo para consulta de produto por codigo MGV6
    EXTERNAL_DB_HOST = os.getenv("EXTERNAL_DB_HOST", "")
    EXTERNAL_DB_PORT = int(os.getenv("EXTERNAL_DB_PORT", "5432"))
    EXTERNAL_DB_NAME = os.getenv("EXTERNAL_DB_NAME", "")
    EXTERNAL_DB_USER = os.getenv("EXTERNAL_DB_USER", "")
    EXTERNAL_DB_PASSWORD = os.getenv("EXTERNAL_DB_PASSWORD", "")
    EXTERNAL_DB_DRIVER = os.getenv("EXTERNAL_DB_DRIVER", "psycopg2")


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/coletor_dama_test",
    )
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
