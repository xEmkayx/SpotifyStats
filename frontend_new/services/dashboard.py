"""
    Kennzahlen und Zeitreihen für das Dashboard.
"""
from sqlalchemy import text
import pandas as pd

from frontend_new.core.db import engine
from frontend_new.core.extensions import cache
from frontend_new.services.sql_fragments import (
    played_at_range_expr, range_params, length_seconds_expr, day_bucket_expr, hour_expr, weekday_expr,
    canonical_song_expr, canonical_join
)

LEN_SEC = length_seconds_expr("s")
RANGE = played_at_range_expr()

KPI_SQL = f"""
SELECT
    COUNT(*) AS streams,
    COALESCE(SUM({LEN_SEC}), 0) AS seconds_total,
    COUNT(DISTINCT {canonical_song_expr()}) AS songs,
    COUNT(DISTINCT s.album_id) AS albums,
    COUNT(DISTINCT {day_bucket_expr()}) AS active_days
FROM stream_history sh
JOIN songs s ON s.song_id = sh.song_id
{canonical_join()}
WHERE {RANGE}
"""

ARTISTS_SQL = f"""
SELECT COUNT(DISTINCT asg.artist_id) AS artists
FROM stream_history sh
JOIN art_songs asg ON asg.song_id = sh.song_id
WHERE {RANGE}
"""

DAILY_SQL = f"""
SELECT {day_bucket_expr()} AS day, COUNT(*) AS plays, COALESCE(SUM({LEN_SEC}), 0) AS seconds_total
FROM stream_history sh
JOIN songs s ON s.song_id = sh.song_id
WHERE {RANGE}
GROUP BY day
ORDER BY day
"""

WEEKDAY_HOUR_SQL = f"""
SELECT {weekday_expr()} AS weekday, {hour_expr()} AS hour, COUNT(*) AS plays
FROM stream_history sh
WHERE {RANGE}
GROUP BY weekday, hour
"""


@cache.memoize(timeout=900)
def dashboard_kpis(start_date: str, end_date: str, cache_version: int) -> dict:
    params = range_params(start_date, end_date)
    with engine.begin() as conn:
        k = dict(conn.execute(text(KPI_SQL), params).mappings().first())
        k["artists"] = conn.execute(text(ARTISTS_SQL), params).scalar() or 0
    return {key: int(val or 0) for key, val in k.items()}


@cache.memoize(timeout=900)
def daily_streams(start_date: str, end_date: str, cache_version: int) -> pd.DataFrame:
    with engine.begin() as conn:
        rows = conn.execute(text(DAILY_SQL), range_params(start_date, end_date)).mappings().all()
    df = pd.DataFrame([dict(r) for r in rows], columns=["day", "plays", "seconds_total"])
    if not df.empty:
        df["day"] = pd.to_datetime(df["day"], format="%Y-%m-%d")
        df["plays"] = df["plays"].astype(int)
        df["seconds_total"] = df["seconds_total"].astype(float)
    return df


@cache.memoize(timeout=900)
def weekday_hour_streams(start_date: str, end_date: str, cache_version: int) -> pd.DataFrame:
    with engine.begin() as conn:
        rows = conn.execute(text(WEEKDAY_HOUR_SQL), range_params(start_date, end_date)).mappings().all()
    df = pd.DataFrame([dict(r) for r in rows], columns=["weekday", "hour", "plays"])
    return df.astype(int) if not df.empty else df


def db_status() -> dict:
    # Nicht gecacht: Settings-Seite soll den echten Stand zeigen
    sql = """
    SELECT
        (SELECT COUNT(*) FROM stream_history) AS streams,
        (SELECT MIN(played_at) FROM stream_history) AS first_stream,
        (SELECT MAX(played_at) FROM stream_history) AS last_stream,
        (SELECT COUNT(*) FROM songs) AS songs,
        (SELECT COUNT(*) FROM artists) AS artists,
        (SELECT COUNT(*) FROM albums) AS albums
    """
    with engine.begin() as conn:
        return dict(conn.execute(text(sql)).mappings().first())
