from sqlalchemy import text
import pandas as pd
from frontend_new.core.db import engine
from frontend_new.core.extensions import cache
from frontend_new.services.sql_fragments import plays_per_song_sql, artists_of_album_expr, range_params, order_column


# Erst pro Album aggregieren + limitieren, dann Album-Artists nur für die Top-N
def _top_albums_sql(order_col: str) -> str:
    return f"""
    SELECT
      al.album_id,
      al.album_name,
      COALESCE({artists_of_album_expr("al.album_id")}, '') AS artists,
      t.plays,
      t.seconds_total
    FROM (
      SELECT s.album_id, SUM(p.plays) AS plays, SUM(p.seconds_total) AS seconds_total
      FROM ({plays_per_song_sql()}) p
      JOIN songs s ON s.song_id = p.song_id
      GROUP BY s.album_id
      ORDER BY {order_col} DESC
      LIMIT :limit
    ) t
    JOIN albums al ON al.album_id = t.album_id
    ORDER BY t.{order_col} DESC
    """

def _fetch_top_albums(start_dt: str, end_dt: str, limit: int, metric: str) -> pd.DataFrame:
    sql = _top_albums_sql(order_column(metric))
    with engine.begin() as conn:
        rows = conn.execute(
            text(sql),
            {**range_params(start_dt, end_dt), "limit": int(limit)}
        ).mappings().all()
    return pd.DataFrame([dict(r) for r in rows])

@cache.memoize(timeout=900)
def cached_top_albums(start_dt: str, end_dt: str, limit: int, metric: str, cache_version: int) -> pd.DataFrame:
    return _fetch_top_albums(start_dt, end_dt, limit, metric)
