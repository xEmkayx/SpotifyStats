from sqlalchemy import text
import pandas as pd
from frontend_new.core.db import engine
from frontend_new.core.extensions import cache

from frontend_new.services.sql_fragments import played_at_cast_expr, length_seconds_expr, artists_agg_left_join

# SQL mit serverseitiger Aggregation und Artists-Zusammenfassung
# WICHTIG: keine User-Inputs in f-string, nur feste SQL-Fragmente

CAST_EXPR = played_at_cast_expr()
LEN_SEC = length_seconds_expr("s")
ARTISTS_JOIN = artists_agg_left_join("s", "aa")
PLAYS_SUBQUERY = f"""
SELECT sh.song_id, COUNT(DISTINCT sh.played_at) AS plays
FROM stream_history sh
WHERE {CAST_EXPR} BETWEEN :start_dt AND :end_dt
GROUP BY sh.song_id
"""
BASE_TOP_SONGS_SQL = f"""
SELECT
s.song_id,
s.song_name,
COALESCE(aa.artists, '') AS artists,
p.plays,
(p.plays * MAX({LEN_SEC})) AS seconds_total
FROM ({PLAYS_SUBQUERY}) p
JOIN songs s ON s.song_id = p.song_id
{ARTISTS_JOIN}
GROUP BY s.song_id, s.song_name, aa.artists, p.plays
"""


def _fetch_top_songs(start_dt: str, end_dt: str, limit: int, metric: str) -> pd.DataFrame:
    metric = (metric or "plays").lower()
    order_col = "plays" if metric == "plays" else "seconds_total"
    sql = BASE_TOP_SONGS_SQL + f" ORDER BY {order_col} DESC LIMIT :limit"
    with engine.begin() as conn:
        rows = conn.execute(
        text(sql),
        {"start_dt": start_dt, "end_dt": end_dt, "limit": limit}
        ).mappings().all()
    return pd.DataFrame([dict(r) for r in rows])


@cache.memoize(timeout=900)
def cached_top_songs(start_dt: str, end_dt: str, limit: int, metric: str, cache_version: int) -> pd.DataFrame:
    return _fetch_top_songs(start_dt, end_dt, limit, metric)


def top_song_ids(start_dt: str, end_dt: str, limit: int, metric: str, cache_version: int) -> list[str]:
    df = cached_top_songs(start_dt, end_dt, limit, metric, cache_version)
    if df.empty:
        return []
    order_col = "plays" if (metric or "plays") == "plays" else "seconds_total"
    df = df.sort_values(order_col, ascending=False)
    # Reihenfolge bewahren, Duplikate entfernen
    seen, out = set(), []
    for x in df["song_id"].tolist():
        if x not in seen:
            seen.add(x); out.append(x)
    return out