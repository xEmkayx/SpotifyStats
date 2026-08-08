from sqlalchemy import text

from frontend_new.core.db import engine
from frontend_new.services.sql_fragments import played_at_cast_expr, length_seconds_expr
from frontend_new.core.extensions import cache

CAST_EXPR = played_at_cast_expr()
LEN_SEC = length_seconds_expr("s")

TOTAL_LISTEN_SQL = f"""
SELECT COALESCE(SUM({LEN_SEC}), 0) AS seconds_total
FROM stream_history sh
JOIN songs s ON s.song_id = sh.song_id
WHERE {CAST_EXPR} BETWEEN :start_dt AND :end_dt
"""

def _fetch_total_listening_seconds(start_dt: str, end_dt: str) -> int:
    with engine.begin() as conn:
        row = conn.execute(text(TOTAL_LISTEN_SQL), {"start_dt": start_dt, "end_dt": end_dt}).mappings().first()
        return int(row["seconds_total"] or 0)


@cache.memoize(timeout=900)
def cached_total_listening_seconds(start_dt: str, end_dt: str, cache_version: int) -> int:
    return _fetch_total_listening_seconds(start_dt, end_dt)

def format_duration_de(seconds: int) -> str:
    # 1d = 86400s
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days: parts.append(f"{days} Tage")
    if hours: parts.append(f"{hours} Stunden")
    if minutes: parts.append(f"{minutes} Minuten")
    if secs or not parts: parts.append(f"{secs} Sekunden")
    return ", ".join(parts)
