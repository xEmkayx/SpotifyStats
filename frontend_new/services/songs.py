from sqlalchemy import text
from frontend_new.core.db import engine
from frontend_new.core.extensions import cache

# Liste für Dropdown: Label "Song – Artists"
SQL = """
SELECT s.song_id,
       s.song_name,
       COALESCE(aa.artists, '') AS artists
FROM songs s
LEFT JOIN (
    SELECT asg.song_id, GROUP_CONCAT(DISTINCT ar.artist_name ORDER BY ar.artist_name SEPARATOR ', ') AS artists
    FROM art_songs asg
    JOIN artists ar ON ar.artist_id = asg.artist_id
    GROUP BY asg.song_id
) aa ON aa.song_id = s.song_id
"""


@cache.memoize(timeout=1800)
def song_options() -> list[dict]:
    with engine.begin() as conn:
        rows = conn.execute(text(SQL)).mappings().all()
    opts = []
    for r in rows:
        label = f"{r['song_name']}" + (f" – {r['artists']}" if r['artists'] else "")
        opts.append({"label": label, "value": r["song_id"]})
    return opts
