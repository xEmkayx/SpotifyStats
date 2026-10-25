"""
    Veraltete Versionen in vielen Playlists auf einmal austauschen – auf Knopfdruck
    (im Hintergrund, mit Fortschritt) oder automatisch nach jedem Playlist-Abgleich.
"""
import logging
import threading
import time

import spotipy
from sqlalchemy import text, bindparam

from common import settings
from common.db.engine import engine
from common.playlists import actions, history

STATUS_KEY = "playlist_replace_status"
# Kurze Rate-Limit-Pausen abwarten, bei längeren den Lauf beenden (Rest beim nächsten Abgleich)
MAX_WAIT_SEC = 60
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


def superseded_totals() -> dict:
    """Einträge gesamt (ein Song in 5 Playlists zählt 5-mal) und verschiedene Songs."""
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT COUNT(*) AS entries, COUNT(DISTINCT i.track_id) AS songs, COUNT(DISTINCT p.playlist_id) AS playlists
            FROM playlists p
            JOIN (SELECT playlist_id, MAX(id) AS id FROM playlist_snapshots GROUP BY playlist_id) ps
                 ON ps.playlist_id = p.playlist_id
            JOIN playlist_snapshot_items i ON i.snapshot_id = ps.id
            LEFT JOIN songs s ON s.song_id = i.track_id
            WHERE p.deleted_at IS NULL AND i.is_local = 0
              AND (i.playable_id IS NOT NULL OR s.relinked_to IS NOT NULL)
        """)).mappings().first()
    return {k: int(v or 0) for k, v in dict(row).items()}


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
    result = {"done": 0, "songs": 0, "skipped": [], "failed": [], "paused": None}
    try:
        # Lieblingssongs zuletzt: dort braucht es eine eigene Berechtigung
        playlist_ids = sorted(playlist_ids, key=lambda p: p == history.LIKED_ID)
        names = _names(playlist_ids)
        total = len(playlist_ids)
        for n, pid in enumerate(playlist_ids, start=1):
            _set_status(f"läuft: {n} von {total} Playlists ({names.get(pid, pid)})")
            todo, digest = actions.superseded_items(pid)
            if not todo:
                continue
            if pid == history.LIKED_ID and not actions.can_modify_library(sp):
                result["skipped"].append(pid)
                continue
            for attempt in (1, 2):
                try:
                    before = len(todo)
                    actions.replace_superseded(sp, pid, digest)
                    after = len(actions.superseded_items(pid)[0])
                    result["done"] += 1
                    result["songs"] += before - after
                except spotipy.SpotifyException as e:
                    if e.http_status != 429:
                        result["failed"].append(pid)
                        logging.exception(f"Austausch in {pid} fehlgeschlagen")
                        break
                    wait = _retry_after(e)
                    if attempt == 1 and wait <= MAX_WAIT_SEC:
                        logging.info(f"Spotify bremst, warte {wait} s")
                        time.sleep(wait + 1)
                        todo, digest = actions.superseded_items(pid)
                        continue
                    result["paused"] = wait
                except actions.PlaylistActionError as e:
                    # z. B. zwischenzeitlich geändert -> beim nächsten Lauf erneut
                    result["skipped"].append(pid)
                    logging.info(f"Austausch in {pid} übersprungen: {e}")
                except Exception:
                    result["failed"].append(pid)
                    logging.exception(f"Austausch in {pid} fehlgeschlagen")
                break
            if result["paused"] is not None:
                break
            time.sleep(0.3)
        summary = f"fertig: {result['songs']} Songs in {result['done']} Playlists ausgetauscht"
        if result["paused"] is not None:
            minutes = max(1, round(result["paused"] / 60))
            summary = (f"pausiert: Spotify bremst gerade (etwa {minutes} Min.). {result['songs']} Songs in "
                       f"{result['done']} Playlists sind schon ausgetauscht, der Rest folgt später")
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


def _names(playlist_ids: list[str]) -> dict:
    if not playlist_ids:
        return {}
    with engine.connect() as conn:
        return dict(conn.execute(text("SELECT playlist_id, name FROM playlists WHERE playlist_id IN :ids")
                                 .bindparams(bindparam("ids", expanding=True)), {"ids": list(playlist_ids)}).all())


def _retry_after(e: spotipy.SpotifyException) -> int:
    try:
        return int((e.headers or {}).get("Retry-After", 60))
    except (TypeError, ValueError):
        return 60


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
