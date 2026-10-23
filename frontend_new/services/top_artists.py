from sqlalchemy import text
import pandas as pd
from frontend_new.core.db import engine
from frontend_new.core.extensions import cache
from frontend_new.services.sql_fragments import plays_per_song_sql, range_params, order_column


# Aggregation auf Artist-Ebene (ein Song mit 2 Artists zählt für beide)
def _top_artists_sql(order_col: str) -> str:
    return f"""
    SELECT
      ar.artist_id,
      ar.artist_name,
      SUM(p.plays) AS plays,
      SUM(p.seconds_total) AS seconds_total
    FROM ({plays_per_song_sql()}) p
    JOIN art_songs asg ON asg.song_id = p.song_id
    JOIN artists ar    ON ar.artist_id = asg.artist_id
    GROUP BY ar.artist_id, ar.artist_name
    ORDER BY {order_col} DESC
    LIMIT :limit
    """


def _fetch_top_artists(start_dt: str, end_dt: str, limit: int, metric: str) -> pd.DataFrame:
    sql = _top_artists_sql(order_column(metric))
    with engine.begin() as conn:
        rows = conn.execute(
            text(sql),
            {**range_params(start_dt, end_dt), "limit": int(limit)}
        ).mappings().all()
    return pd.DataFrame([dict(r) for r in rows])

@cache.memoize(timeout=900)
def cached_top_artists(start_dt: str, end_dt: str, limit: int, metric: str, cache_version: int) -> pd.DataFrame:
    return _fetch_top_artists(start_dt, end_dt, limit, metric)
