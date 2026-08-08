from sqlalchemy import text
from frontend_new.core.db import engine
from frontend_new.core.extensions import cache

SEARCH_SQL = """
SELECT s.song_id,
       s.song_name,
       COALESCE(aa.artists, '') AS artists
FROM songs s
LEFT JOIN (
    SELECT asg.song_id,
           GROUP_CONCAT(DISTINCT ar.artist_name ORDER BY ar.artist_name SEPARATOR ', ') AS artists
    FROM art_songs asg
    JOIN artists ar ON ar.artist_id = asg.artist_id
    GROUP BY asg.song_id
) aa ON aa.song_id = s.song_id
WHERE ({where_clause})
ORDER BY s.song_name
LIMIT :limit
"""

GET_BY_ID_SQL = """
SELECT s.song_id,
       s.song_name,
       COALESCE(aa.artists, '') AS artists
FROM songs s
LEFT JOIN (
    SELECT asg.song_id,
           GROUP_CONCAT(DISTINCT ar.artist_name ORDER BY ar.artist_name SEPARATOR ', ') AS artists
    FROM art_songs asg
    JOIN artists ar ON ar.artist_id = asg.artist_id
    GROUP BY asg.song_id
) aa ON aa.song_id = s.song_id
WHERE s.song_id = :song_id
"""

def _escape_like(term: str, esc: str = "!") -> str:
    return (term
            .replace(esc, esc + esc)
            .replace("%", esc + "%")
            .replace("_", esc + "_"))

def _build_where(tokens: list[str]) -> tuple[str, dict]:
    clauses = []
    params = {}
    for i, t in enumerate(tokens):
        p = f"p{i}"
        clauses.append(
            f"(s.song_name LIKE :{p} ESCAPE '!' OR COALESCE(aa.artists, '') LIKE :{p} ESCAPE '!')"
        )
        params[p] = f"%{_escape_like(t)}%"
    where_clause = " AND ".join(clauses) if clauses else "1=1"
    return where_clause, params

@cache.memoize(timeout=60)
def search_songs(query: str, limit: int = 50) -> list[dict]:
    q = (query or "").strip()
    if len(q) < 2:
        return []
    tokens = [t for t in q.split() if t]
    where_clause, params = _build_where(tokens)
    sql = SEARCH_SQL.replace("{where_clause}", where_clause)
    with engine.begin() as conn:
        rows = conn.execute(text(sql), {**params, "limit": int(limit)}).mappings().all()
    return [
        {"label": f"{r['song_name']}" + (f" – {r['artists']}" if r['artists'] else ""), "value": r["song_id"]}
        for r in rows
    ]

@cache.memoize(timeout=300)
def get_song_option_by_id(song_id: str) -> dict | None:
    if not song_id:
        return None
    with engine.begin() as conn:
        row = conn.execute(text(GET_BY_ID_SQL), {"song_id": song_id}).mappings().first()
    if not row:
        return None
    label = f"{row['song_name']}" + (f" – {row['artists']}" if row['artists'] else "")
    return {"label": label, "value": row["song_id"]}
