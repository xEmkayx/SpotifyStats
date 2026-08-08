from sqlalchemy import text
import pandas as pd
from frontend_new.core.db import engine
from frontend_new.core.extensions import cache
from frontend_new.services.sql_fragments import played_at_cast_expr, day_bucket_expr

CAST_EXPR = played_at_cast_expr()
DAY_EXPR = day_bucket_expr()

BASE_SQL = f"""
SELECT {DAY_EXPR} AS day, COUNT(*) AS plays
FROM stream_history sh
WHERE sh.song_id = :song_id
  AND {CAST_EXPR} BETWEEN :start_dt AND :end_dt
GROUP BY day
ORDER BY day
"""


def _fetch_daily_song_counts(song_id: str, year: int) -> pd.DataFrame:
    start_dt = f"{int(year)}-01-01 00:00"
    end_dt   = f"{int(year)}-12-31 23:59"
    with engine.begin() as conn:
        rows = conn.execute(
            text(BASE_SQL),
            {"song_id": song_id, "start_dt": start_dt, "end_dt": end_dt}
        ).mappings().all()
    df = pd.DataFrame([dict(r) for r in rows])
    # day als date normalisieren
    if not df.empty:
        df["day"] = pd.to_datetime(df["day"]).dt.date
    return df


@cache.memoize(timeout=900)
def cached_daily_song_counts(song_id: str, year: int, cache_version: int) -> pd.DataFrame:
    return _fetch_daily_song_counts(song_id, int(year))
