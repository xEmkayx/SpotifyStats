"""
    Streams pro Song, gefiltert nach Artist, Album oder Songtitel (Name oder ID).
    Ersetzt die alten Seiten single_artist/single_album/single_song_streams.
"""
from sqlalchemy import text
import pandas as pd

from frontend_new.core.db import engine
from frontend_new.core.extensions import cache
from frontend_new.services.song_search import _escape_like
from frontend_new.services.sql_fragments import plays_per_song_sql, artists_of_song_expr, range_params, order_column

# (Kategorie, Match-Art) -> (WHERE-Fragment, braucht albums-Join, LIKE?)
_FILTERS = {
    ("song", "name"): ("s.song_name LIKE :q ESCAPE '!'", False, True),
    ("song", "id"): ("s.song_id = :q", False, False),
    ("album", "name"): ("al.album_name LIKE :q ESCAPE '!'", True, True),
    ("album", "id"): ("s.album_id = :q", False, False),
    ("artist", "name"): ("EXISTS (SELECT 1 FROM art_songs asg2 JOIN artists ar2 ON ar2.artist_id = asg2.artist_id "
                         "WHERE asg2.song_id = sh.song_id AND ar2.artist_name LIKE :q ESCAPE '!')", False, True),
    ("artist", "id"): ("EXISTS (SELECT 1 FROM art_songs asg2 "
                       "WHERE asg2.song_id = sh.song_id AND asg2.artist_id = :q)", False, False),
}


@cache.memoize(timeout=900)
def entity_song_streams(category: str, match: str, query: str, start_date: str, end_date: str,
                        limit: int, metric: str, cache_version: int) -> pd.DataFrame:
    query = (query or "").strip()
    key = (category or "artist", match or "name")
    if not query or key not in _FILTERS:
        return pd.DataFrame()
    where, needs_album, is_like = _FILTERS[key]
    extra_join = "JOIN albums al ON al.album_id = s.album_id" if needs_album else ""
    order_col = order_column(metric)
    sql = f"""
    SELECT
        t.song_id,
        s.song_name,
        COALESCE({artists_of_song_expr("t.song_id")}, '') AS artists,
        al.album_name,
        t.plays,
        t.seconds_total
    FROM (
        {plays_per_song_sql(extra_where=where, extra_join=extra_join)}
        ORDER BY {order_col} DESC
        LIMIT :limit
    ) t
    JOIN songs s ON s.song_id = t.song_id
    LEFT JOIN albums al ON al.album_id = s.album_id
    ORDER BY t.{order_col} DESC
    """
    params = {**range_params(start_date, end_date), "limit": int(limit),
              "q": f"%{_escape_like(query)}%" if is_like else query}
    with engine.begin() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
    return pd.DataFrame([dict(r) for r in rows])
