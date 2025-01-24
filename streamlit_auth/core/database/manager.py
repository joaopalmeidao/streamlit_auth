import os
from sqlalchemy import create_engine

from streamlit_auth.config import settings


def get_engine(db_uri=None):
    db_uri = db_uri or settings.DB_URI
    return create_engine(
        db_uri,
        isolation_level='SERIALIZABLE',
        echo=False
    )

default_engine = get_engine()
