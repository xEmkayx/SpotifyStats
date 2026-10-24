"""
    Daten für die Playlist-Seite: Übersicht, Verlauf (Snapshots) und Diffs.
"""
from datetime import timezone
from zoneinfo import ZoneInfo

from sqlalchemy import text

from common.playlists import history
from frontend_new.config import DISPLAY_TZ
from frontend_new.core.db import engine
from frontend_new.core.extensions import cache
from frontend_new.services.song_search import _escape_like

_TZ = ZoneInfo(DISPLAY_TZ)

_SORTS = {
    "changed": "COALESCE(p.last_changed_at, p.first_seen_at) DESC",
    "name": "p.name ASC",
    "tracks": "p.track_count DESC",
    "superseded": "superseded DESC, p.name ASC",
}


def count(n, singular: str, plural: str) -> str:
    # "1 Song" / "3 Songs", Tausenderpunkt wie im Deutschen üblich
    n = int(n or 0)
    return f"{n:,}".replace(",", ".") + " " + (singular if n == 1 else plural)


def local_time(value, fmt: str = "%d.%m.%Y %H:%M") -> str:
    if not value:
        return "—"
    return value.replace(tzinfo=timezone.utc).astimezone(_TZ).strftime(fmt)


# Einträge im letzten Snapshot, die Spotify auf eine neuere Version umleitet
_SUPERSEDED_SQL = """
    SELECT ps.playlist_id, COUNT(*) AS superseded
    FROM (SELECT playlist_id, MAX(id) AS id FROM playlist_snapshots GROUP BY playlist_id) ps
    JOIN playlist_snapshot_items i ON i.snapshot_id = ps.id
    LEFT JOIN songs s ON s.song_id = i.track_id
    WHERE i.is_local = 0 AND (i.playable_id IS NOT NULL OR s.relinked_to IS NOT NULL)
    GROUP BY ps.playlist_id
"""


@cache.memoize(timeout=300)
def playlist_overview(search: str, sort: str, include_deleted: bool, cache_version: int) -> list[dict]:
    where, params = ["1=1"], {}
    if search:
        where.append("p.name LIKE :q ESCAPE '!'")
        params["q"] = f"%{_escape_like(search)}%"
    if not include_deleted:
        where.append("p.deleted_at IS NULL")
    sql = f"""
        SELECT p.playlist_id, p.name, p.track_count, p.image_url, p.is_public, p.first_seen_at, p.last_synced_at,
               p.last_changed_at, p.deleted_at, COALESCE(sup.superseded, 0) AS superseded,
               (SELECT COUNT(*) FROM playlist_snapshots s WHERE s.playlist_id = p.playlist_id) AS snapshots
        FROM playlists p
        LEFT JOIN ({_SUPERSEDED_SQL}) sup ON sup.playlist_id = p.playlist_id
        WHERE {" AND ".join(where)}
        ORDER BY p.playlist_id = :liked DESC, {_SORTS.get(sort, _SORTS["changed"])}
    """
    with engine.connect() as conn:
        return [dict(r) for r in conn.execute(text(sql), {**params, "liked": history.LIKED_ID}).mappings()]


def playlist_info(playlist_id: str):
    with engine.connect() as conn:
        row = conn.execute(text("SELECT * FROM playlists WHERE playlist_id = :p"), {"p": playlist_id}).mappings().first()
        return dict(row) if row else None


def snapshots(playlist_id: str) -> list[dict]:
    with engine.connect() as conn:
        return [dict(r) for r in conn.execute(text("""
            SELECT id, spotify_snapshot_id, name, description, track_count, content_hash, reason, taken_at
            FROM playlist_snapshots WHERE playlist_id = :p ORDER BY id DESC
        """), {"p": playlist_id}).mappings()]


@cache.memoize(timeout=86400)
def snapshot_diff(old_pk: int, new_pk: int) -> list[dict]:
    # Snapshots sind unveränderlich -> Diff darf lange gecacht werden
    with engine.connect() as conn:
        old = history.snapshot_items(conn, old_pk) if old_pk else []
        new = history.snapshot_items(conn, new_pk)
    return history.diff_items(old, new)


def diff_summary(changes: list[dict]) -> dict:
    out = {"added": 0, "removed": 0, "moved": 0, "replaced": 0}
    for c in changes:
        out[c["op"]] += 1
    return out
