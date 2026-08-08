from sqlalchemy import text
import pandas as pd
from frontend_new.core.db import engine
from frontend_new.core.extensions import cache
from frontend_new.services.sql_fragments import played_at_cast_expr, length_seconds_expr

CAST = played_at_cast_expr()
LEN  = length_seconds_expr("s")

PLAYS_PER_SONG = f"""
SELECT sh.song_id, COUNT(DISTINCT sh.played_at) AS plays
FROM stream_history sh
WHERE {CAST} BETWEEN :start_dt AND :end_dt
GROUP BY sh.song_id
"""
# Songs (mit Artists-String + Album)

SQL_TOP_SONGS = f"""
WITH p AS ({PLAYS_PER_SONG})
SELECT
s.song_id,
s.song_name,
al.album_id,
al.album_name,
-- Artists pro Song voraggregiert (kein Overcount)
(
SELECT GROUP_CONCAT(DISTINCT ar.artist_name ORDER BY ar.artist_name SEPARATOR ', ')
FROM art_songs asg JOIN artists ar ON ar.artist_id = asg.artist_id
WHERE asg.song_id = s.song_id
) AS artists,
p.plays,
(p.plays * {LEN}) AS seconds_total
FROM p
JOIN songs s   ON s.song_id = p.song_id
JOIN albums al ON al.album_id = s.album_id
"""
# Artists

SQL_TOP_ARTISTS = f"""
WITH p AS ({PLAYS_PER_SONG})
SELECT
ar.artist_id,
ar.artist_name,
SUM(p.plays) AS plays,
SUM(p.plays * {LEN}) AS seconds_total
FROM p
JOIN songs s       ON s.song_id = p.song_id
JOIN art_songs asg ON asg.song_id = s.song_id
JOIN artists ar    ON ar.artist_id = asg.artist_id
GROUP BY ar.artist_id, ar.artist_name
"""
# Alben (inkl. Artists-String pro Album)

SQL_TOP_ALBUMS = f"""
WITH p AS ({PLAYS_PER_SONG})
SELECT
al.album_id,
al.album_name,
(
SELECT GROUP_CONCAT(DISTINCT ar.artist_name ORDER BY ar.artist_name SEPARATOR ', ')
FROM album_artists aa JOIN artists ar ON ar.artist_id = aa.artist_id
WHERE aa.album_id = al.album_id
) AS artists,
SUM(p.plays) AS plays,
SUM(p.plays * {LEN}) AS seconds_total
FROM p
JOIN songs s   ON s.song_id = p.song_id
JOIN albums al ON al.album_id = s.album_id
GROUP BY al.album_id, al.album_name
"""

def _fetch_df(base_sql: str, start_dt: str, end_dt: str, limit: int, metric: str) -> pd.DataFrame:
    order_col = "plays" if (metric or "plays") == "plays" else "seconds_total"
    sql = base_sql + f" ORDER BY {order_col} DESC LIMIT :limit"
    with engine.begin() as conn:
        rows = conn.execute(text(sql), {"start_dt": start_dt, "end_dt": end_dt, "limit": int(limit)}).mappings().all()
    return pd.DataFrame([dict(r) for r in rows])

@cache.memoize(timeout=900)
def top_songs_data(start_dt, end_dt, limit, metric, cache_version):
    return _fetch_df(SQL_TOP_SONGS, start_dt, end_dt, limit, metric)

@cache.memoize(timeout=900)
def top_artists_data(start_dt, end_dt, limit, metric, cache_version):
    return _fetch_df(SQL_TOP_ARTISTS, start_dt, end_dt, limit, metric)

@cache.memoize(timeout=900)
def top_albums_data(start_dt, end_dt, limit, metric, cache_version):
    return _fetch_df(SQL_TOP_ALBUMS, start_dt, end_dt, limit, metric)
