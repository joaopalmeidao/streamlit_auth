import os
from sqlalchemy import create_engine, text
import logging

from streamlit_auth.config import settings


logger = logging.getLogger(settings.MAIN_LOGGER_NAME)

def get_engine(db_uri=None):
    db_uri = db_uri or settings.DB_URI
    return create_engine(
        db_uri,
        isolation_level='SERIALIZABLE',
        echo=False
    )

default_engine = get_engine()

def execute_query(query: str, engine = default_engine, params: dict = None):
    try:
        with engine.begin() as con:
            result = con.execute(text(query), params)
        return result
    except Exception as e:
        logger.error(f"Erro na execução da query: {e}", exc_info=True)
        return None
