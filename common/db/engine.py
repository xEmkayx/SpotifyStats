"""
    Gemeinsame SQLAlchemy-Engine für Backend und Frontend.

    pool_pre_ping verhindert "MySQL server has gone away" nach wait_timeout,
    was bei der alten, dauerhaft offenen mysql.connector-Verbindung passiert.
"""
from sqlalchemy import create_engine

from common.config.config import MYSQL_URL

engine = create_engine(
    MYSQL_URL,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=3600,
    future=True,
)
