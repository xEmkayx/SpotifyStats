from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

from common.config.config import MYSQL_URL

engine = create_engine(
    MYSQL_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
    future=True,
)
