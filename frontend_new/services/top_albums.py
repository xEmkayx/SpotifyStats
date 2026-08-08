from sqlalchemy import text
import pandas as pd
from frontend_new.core.db import engine
from frontend_new.core.extensions import cache
from frontend_new.services.sql_fragments import played_at_cast_expr, length_seconds_expr, album_artists_agg_left_join

CAST_EXPR = played_at_cast_expr()
LEN_SEC = length_seconds_expr("s")
ALB_ARTISTS_JOIN = album_artists_agg_left_join("al", "aa")

PLAYS_SUBQUERY = f"""
SELECT sh.song_id, COUNT(DISTINCT sh.played_at) AS plays
FROM stream_history sh
WHERE {CAST_EXPR} BETWEEN :start_dt AND :end_dt
GROUP BY sh.song_id
"""

BASE_TOP_ALBUMS_SQL = f"""
SELECT
  al.album_id,
  al.album_name,
  COALESCE(aa.artists, '') AS artists,
  SUM(p.plays) AS plays,
  SUM(p.plays * {LEN_SEC}) AS seconds_total
FROM ({PLAYS_SUBQUERY}) p
JOIN songs s  ON s.song_id  = p.song_id
JOIN albums al ON al.album_id = s.album_id
{ALB_ARTISTS_JOIN}
GROUP BY al.album_id, al.album_name, aa.artists
"""

def _fetch_top_albums(start_dt: str, end_dt: str, limit: int, metric: str) -> pd.DataFrame:
    metric = (metric or "plays").lower()
    order_col = "plays" if metric == "plays" else "seconds_total"
    sql = BASE_TOP_ALBUMS_SQL + f" ORDER BY {order_col} DESC LIMIT :limit"
    with engine.begin() as conn:
        rows = conn.execute(
            text(sql),
            {"start_dt": start_dt, "end_dt": end_dt, "limit": limit}
        ).mappings().all()
    return pd.DataFrame([dict(r) for r in rows])

@cache.memoize(timeout=900)
def cached_top_albums(start_dt: str, end_dt: str, limit: int, metric: str, cache_version: int) -> pd.DataFrame:
    return _fetch_top_albums(start_dt, end_dt, limit, metric)
