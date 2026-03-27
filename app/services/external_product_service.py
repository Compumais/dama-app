import os

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


_engine = None


def _build_external_database_url() -> str:
    host = os.getenv("EXTERNAL_DB_HOST", "").strip()
    port = os.getenv("EXTERNAL_DB_PORT", "5432").strip()
    database = os.getenv("EXTERNAL_DB_NAME", "").strip()
    username = os.getenv("EXTERNAL_DB_USER", "").strip()
    password = os.getenv("EXTERNAL_DB_PASSWORD", "").strip()
    driver = os.getenv("EXTERNAL_DB_DRIVER", "psycopg2").strip()

    if not all([host, port, database, username, password]):
        return ""
    return f"postgresql+{driver}://{username}:{password}@{host}:{port}/{database}"


def _get_engine():
    global _engine
    if _engine is not None:
        return _engine

    database_url = _build_external_database_url()
    if not database_url:
        return None

    _engine = create_engine(database_url, pool_pre_ping=True)
    return _engine


def get_external_product_by_code(product_code: str):
    engine = _get_engine()
    if engine is None:
        return None

    sql = text(
        """
        SELECT CAST(codigo AS TEXT) AS codigo, nome
        FROM produto
        WHERE CAST(codigo AS TEXT) = :codigo
           OR LTRIM(CAST(codigo AS TEXT), '0') = :codigo_sem_zero
        LIMIT 1
        """
    )
    try:
        with engine.connect() as connection:
            row = connection.execute(
                sql,
                {
                    "codigo": product_code,
                    "codigo_sem_zero": product_code.lstrip("0"),
                },
            ).first()
            if not row:
                return None
            external_code = (row[0] or "").strip()
            external_name = (row[1] or "").strip()
            if not external_name:
                return None
            return {
                "codigo": external_code or product_code,
                "nome": external_name,
            }
    except SQLAlchemyError:
        return None


def get_external_product_name_by_code(product_code: str) -> str | None:
    product = get_external_product_by_code(product_code)
    if not product:
        return None
    return product["nome"]
