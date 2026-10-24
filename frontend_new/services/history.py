"""
    Hörhistorie: einzelne Streams im Zeitraum, serverseitig paginiert.
"""
from sqlalchemy import text
import pandas as pd

from frontend_new.core.db import engine
from frontend_new.core.extensions import cache
from frontend_new.services.song_search import _escape_like
from frontend_new.services.sql_fragments import (
    played_at_range_expr, range_params, length_seconds_expr, artists_of_song_expr, local_time_expr
)

LEN_SEC = length_seconds_expr("s")

SEARCH_CLAUSE = """
    s.song_name LIKE :q ESCAPE '!'
    OR al.album_name LIKE :q ESCAPE '!'
    OR EXISTS (
        SELECT 1 FROM art_songs asg2 JOIN artists ar2 ON ar2.artist_id = asg2.artist_id
        WHERE asg2.song_id = sh.song_id AND ar2.artist_name LIKE :q ESCAPE '!'
    )
"""


def _where(search: str) -> str:
    where = played_at_range_expr()
    if search:
        where += f" AND ({SEARCH_CLAUSE})"
    return where


def _params(start_date, end_date, search: str) -> dict:
    params = range_params(start_date, end_date)
    if search:
        params["q"] = f"%{_escape_like(search)}%"
    return params


@cache.memoize(timeout=900)
def history_totals(start_date: str, end_date: str, search: str, cache_version: int) -> dict:
    search = (search or "").strip()
    sql = f"""
    SELECT COUNT(*) AS streams, COALESCE(SUM({LEN_SEC}), 0) AS seconds_total
    FROM stream_history sh
    JOIN songs s ON s.song_id = sh.song_id
    LEFT JOIN albums al ON al.album_id = s.album_id
    WHERE {_where(search)}
    """
    with engine.begin() as conn:
        row = conn.execute(text(sql), _params(start_date, end_date, search)).mappings().first()
    return {"streams": int(row["streams"] or 0), "seconds_total": int(row["seconds_total"] or 0)}


@cache.memoize(timeout=900)
def history_page(start_date: str, end_date: str, search: str, page: int, page_size: int,
                 cache_version: int) -> pd.DataFrame:
    search = (search or "").strip()
    sql = f"""
    SELECT
        DATE_FORMAT({local_time_expr()}, '%Y-%m-%d %H:%i:%s') AS played_at,
        s.song_name,
        COALESCE({artists_of_song_expr("sh.song_id")}, '') AS artists,
        al.album_name,
        CONCAT(FLOOR(s.duration_ms / 60000), ':', LPAD(MOD(FLOOR(s.duration_ms / 1000), 60), 2, '0'))
            AS song_length,
        sh.song_id
    FROM stream_history sh
    JOIN songs s ON s.song_id = sh.song_id
    LEFT JOIN albums al ON al.album_id = s.album_id
    WHERE {_where(search)}
    ORDER BY sh.played_at DESC
    LIMIT :limit OFFSET :offset
    """
    params = {**_params(start_date, end_date, search),
              "limit": int(page_size), "offset": int(page) * int(page_size)}
    with engine.begin() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
    return pd.DataFrame([dict(r) for r in rows],
                        columns=["played_at", "song_name", "artists", "album_name", "song_length", "song_id"])
