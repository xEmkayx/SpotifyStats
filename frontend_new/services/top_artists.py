from sqlalchemy import text
import pandas as pd
from frontend_new.core.db import engine
from frontend_new.core.extensions import cache
from frontend_new.services.sql_fragments import played_at_cast_expr, length_seconds_expr

CAST_EXPR = played_at_cast_expr()
LEN_SEC = length_seconds_expr("s")

# Plays pro Song-ID im Zeitraum
PLAYS_SUBQUERY = f"""
SELECT sh.song_id, COUNT(DISTINCT sh.played_at) AS plays
FROM stream_history sh
WHERE {CAST_EXPR} BETWEEN :start_dt AND :end_dt
GROUP BY sh.song_id
"""

# Aggregation auf Artist-Ebene
BASE_TOP_ARTISTS_SQL = f"""
SELECT
  ar.artist_id,
  ar.artist_name,
  SUM(p.plays) AS plays,
  SUM(p.plays * {LEN_SEC}) AS seconds_total
FROM ({PLAYS_SUBQUERY}) p
JOIN songs s       ON s.song_id = p.song_id
JOIN art_songs asg ON asg.song_id = s.song_id
JOIN artists ar    ON ar.artist_id = asg.artist_id
GROUP BY ar.artist_id, ar.artist_name
"""

def _fetch_top_artists(start_dt: str, end_dt: str, limit: int, metric: str) -> pd.DataFrame:
    metric = (metric or "plays").lower()
    order_col = "plays" if metric == "plays" else "seconds_total"
    sql = BASE_TOP_ARTISTS_SQL + f" ORDER BY {order_col} DESC LIMIT :limit"
    with engine.begin() as conn:
        rows = conn.execute(
            text(sql),
            {"start_dt": start_dt, "end_dt": end_dt, "limit": limit}
        ).mappings().all()
    return pd.DataFrame([dict(r) for r in rows])

@cache.memoize(timeout=900)
def cached_top_artists(start_dt: str, end_dt: str, limit: int, metric: str, cache_version: int) -> pd.DataFrame:
    return _fetch_top_artists(start_dt, end_dt, limit, metric)
