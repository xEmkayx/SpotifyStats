"""
    Führt die Alembic-Migrationen aus (upgrade head).

    Das Backend ruft upgrade() beim Start auf; das Frontend migriert nie selbst.
    Manuell:  python -m common.db.migrate            (upgrade head)
              alembic -c common/db/alembic.ini ...   (history, downgrade, ...)
"""
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

ALEMBIC_INI = Path(__file__).resolve().parent / "alembic.ini"


def alembic_config() -> Config:
    return Config(str(ALEMBIC_INI))


def upgrade(revision: str = "head"):
    logging.info(f"Alembic: upgrade {revision}")
    command.upgrade(alembic_config(), revision)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    upgrade()
