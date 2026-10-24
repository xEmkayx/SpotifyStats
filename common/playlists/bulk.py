"""
    Veraltete Versionen in vielen Playlists auf einmal austauschen – auf Knopfdruck
    (im Hintergrund, mit Fortschritt) oder automatisch nach jedem Playlist-Abgleich.
"""
import logging
import threading
import time

from sqlalchemy import text

from common import settings
from common.db.engine import engine
from common.playlists import actions, history

STATUS_KEY = "playlist_replace_status"
# MySQL-Sperre statt threading.Lock: Backend (Automatik) und Frontend (Knopf) sind getrennte Prozesse.
# Bricht ein Prozess ab, gibt MySQL die Sperre mit der Verbindung automatisch frei.
_LOCK_NAME = "spotify_stats_playlist_replace"


def superseded_overview() -> list[dict]:
    """Eigene, nicht gelöschte Playlists mit Anzahl der Songs, die eine neuere Version haben."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT p.playlist_id, p.name, COUNT(*) AS superseded
            FROM playlists p
            JOIN (SELECT playlist_id, MAX(id) AS id FROM playlist_snapshots GROUP BY playlist_id) ps
                 ON ps.playlist_id = p.playlist_id
            JOIN playlist_snapshot_items i ON i.snapshot_id = ps.id
            LEFT JOIN songs s ON s.song_id = i.track_id
            WHERE p.deleted_at IS NULL AND i.is_local = 0
              AND (i.playable_id IS NOT NULL OR s.relinked_to IS NOT NULL)
            GROUP BY p.playlist_id, p.name
            ORDER BY superseded DESC
        """)).mappings().all()
    return [dict(r) for r in rows]


def _set_status(value: str):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO sync_state (name, value) VALUES (:n, :v)
            ON DUPLICATE KEY UPDATE value = VALUES(value)
        """), {"n": STATUS_KEY, "v": value[:200]})


def status() -> tuple:
    with engine.connect() as conn:
        row = conn.execute(text("SELECT value, updated_at FROM sync_state WHERE name = :n"),
                           {"n": STATUS_KEY}).first()
    return (row[0], row[1]) if row else (None, None)


def is_running() -> bool:
    with engine.connect() as conn:
        return conn.execute(text("SELECT IS_USED_LOCK(:n)"), {"n": _LOCK_NAME}).scalar() is not None


def replace_many(sp, playlist_ids: list[str]) -> dict:
    """Tauscht in den angegebenen Playlists alle veralteten Versionen aus. Läuft nur einmal gleichzeitig."""
    lock_conn = engine.connect()
    if not lock_conn.execute(text("SELECT GET_LOCK(:n, 0)"), {"n": _LOCK_NAME}).scalar():
        lock_conn.close()
        return {"skipped": True}
    result = {"done": 0, "songs": 0, "skipped": [], "failed": []}
    try:
        total = len(playlist_ids)
        for n, pid in enumerate(playlist_ids, start=1):
            _set_status(f"läuft: {n} von {total} Playlists")
            todo, digest = actions.superseded_items(pid)
            if not todo:
                continue
            if pid == history.LIKED_ID and not actions.can_modify_library(sp):
                result["skipped"].append(pid)
                continue
            try:
                before = len(todo)
                actions.replace_superseded(sp, pid, digest)
                after = len(actions.superseded_items(pid)[0])
                result["done"] += 1
                result["songs"] += before - after
            except actions.PlaylistActionError as e:
                # z. B. lokale Dateien oder zwischenzeitlich geändert -> beim nächsten Lauf erneut
                result["skipped"].append(pid)
                logging.info(f"Austausch in {pid} übersprungen: {e}")
            except Exception:
                result["failed"].append(pid)
                logging.exception(f"Austausch in {pid} fehlgeschlagen")
            time.sleep(0.2)
        summary = f"fertig: {result['songs']} Songs in {result['done']} Playlists ausgetauscht"
        if result["skipped"] or result["failed"]:
            summary += f", {len(result['skipped']) + len(result['failed'])} Playlists übersprungen"
        _set_status(summary)
        return result
    except Exception as e:
        _set_status(f"abgebrochen: {e}")
        raise
    finally:
        lock_conn.execute(text("SELECT RELEASE_LOCK(:n)"), {"n": _LOCK_NAME})
        lock_conn.close()


def replace_many_in_background(sp, playlist_ids: list[str]) -> bool:
    if is_running():
        return False
    threading.Thread(target=replace_many, args=(sp, playlist_ids), name="playlist-replace", daemon=True).start()
    return True


def run_auto_replace(sp) -> dict:
    """Nach dem Playlist-Abgleich: automatisch austauschen, falls in den Einstellungen aktiviert."""
    include_playlists = settings.get_flag(settings.AUTO_REPLACE_PLAYLISTS)
    include_liked = settings.get_flag(settings.AUTO_REPLACE_LIKED)
    if not include_playlists and not include_liked:
        return {"disabled": True}
    ids = [p["playlist_id"] for p in superseded_overview()
           if (p["playlist_id"] == history.LIKED_ID and include_liked)
           or (p["playlist_id"] != history.LIKED_ID and include_playlists)]
    return replace_many(sp, ids) if ids else {"done": 0}
