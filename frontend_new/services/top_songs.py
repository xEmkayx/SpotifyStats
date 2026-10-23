from sqlalchemy import text
import pandas as pd
from frontend_new.core.db import engine
from frontend_new.core.extensions import cache

from frontend_new.services.sql_fragments import plays_per_song_sql, artists_of_song_expr, range_params, order_column

# Erst im Zeitraum aggregieren und auf Top-N limitieren, danach nur für diese
# N Songs Artists/Album nachladen (statt GROUP_CONCAT über alle Songs der DB).
# WICHTIG: keine User-Inputs in f-string, nur feste SQL-Fragmente

def _top_songs_sql(order_col: str) -> str:
    return f"""
    SELECT
        t.song_id,
        s.song_name,
        COALESCE({artists_of_song_expr("t.song_id")}, '') AS artists,
        s.album_id,
        al.album_name,
        t.plays,
        t.seconds_total
    FROM (
        {plays_per_song_sql()}
        ORDER BY {order_col} DESC
        LIMIT :limit
    ) t
    JOIN songs s ON s.song_id = t.song_id
    LEFT JOIN albums al ON al.album_id = s.album_id
    ORDER BY t.{order_col} DESC
    """


def _fetch_top_songs(start_dt: str, end_dt: str, limit: int, metric: str) -> pd.DataFrame:
    sql = _top_songs_sql(order_column(metric))
    with engine.begin() as conn:
        rows = conn.execute(
        text(sql),
        {**range_params(start_dt, end_dt), "limit": int(limit)}
        ).mappings().all()
    return pd.DataFrame([dict(r) for r in rows])


@cache.memoize(timeout=900)
def cached_top_songs(start_dt: str, end_dt: str, limit: int, metric: str, cache_version: int) -> pd.DataFrame:
    return _fetch_top_songs(start_dt, end_dt, limit, metric)


def top_song_ids(start_dt: str, end_dt: str, limit: int, metric: str, cache_version: int) -> list[str]:
    df = cached_top_songs(start_dt, end_dt, limit, metric, cache_version)
    if df.empty:
        return []
    order_col = order_column(metric)
    df = df.sort_values(order_col, ascending=False)
    # Reihenfolge bewahren, Duplikate entfernen
    seen, out = set(), []
    for x in df["song_id"].tolist():
        if x not in seen:
            seen.add(x); out.append(x)
    return out
