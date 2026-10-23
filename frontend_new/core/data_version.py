"""
    Datenversion für Cache-Keys.

    Alle gecachten Services bekommen `cache_version` als Argument. Die Version
    ändert sich automatisch, sobald neue Streams in der DB liegen (COUNT + MAX
    über den PK-Index, ~10 ms), oder manuell über den Refresh-Button.
    Dadurch sind Daten nie älter als DATA_VERSION_TTL_SEC, ohne dass jemand
    einen Reload antriggern muss.
"""
import zlib

from sqlalchemy import text

from frontend_new.config import DATA_VERSION_TTL_SEC
from frontend_new.core.db import engine
from frontend_new.core.extensions import cache

_BUMP_KEY = "data-version-bump"
_FINGERPRINT_KEY = "data-version-fingerprint"


def _db_fingerprint() -> str:
    fp = cache.get(_FINGERPRINT_KEY)
    if fp is None:
        with engine.connect() as conn:
            cnt, last = conn.execute(text("SELECT COUNT(*), MAX(played_at) FROM stream_history")).one()
        fp = f"{cnt}|{last}"
        cache.set(_FINGERPRINT_KEY, fp, timeout=DATA_VERSION_TTL_SEC)
    return fp


def data_version() -> int:
    bump = cache.get(_BUMP_KEY) or 0
    return zlib.crc32(f"{_db_fingerprint()}|{bump}".encode())


def bump_data_version() -> int:
    # Erzwingt neue Cache-Keys, auch wenn sich die Streams nicht geändert haben
    cache.set(_BUMP_KEY, (cache.get(_BUMP_KEY) or 0) + 1, timeout=0)
    cache.delete(_FINGERPRINT_KEY)
    return data_version()
