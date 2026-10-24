"""
    Einstellungen aus der Oberfläche (Tabelle app_settings), von Backend und Frontend gelesen.
"""
from sqlalchemy import text

from common.db.engine import engine

AUTO_REPLACE_PLAYLISTS = "auto_replace_playlists"
AUTO_REPLACE_LIKED = "auto_replace_liked"


def get_setting(name: str, default: str = None) -> str:
    with engine.connect() as conn:
        value = conn.execute(text("SELECT value FROM app_settings WHERE name = :n"), {"n": name}).scalar()
    return default if value is None else value


def get_flag(name: str) -> bool:
    return get_setting(name, "0") == "1"


def set_setting(name: str, value: str):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app_settings (name, value) VALUES (:n, :v)
            ON DUPLICATE KEY UPDATE value = VALUES(value)
        """), {"n": name, "v": value})


def set_flag(name: str, enabled: bool):
    set_setting(name, "1" if enabled else "0")
