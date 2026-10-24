"""
    Abgleich des lokalen Katalogs mit Spotify.

    Nutzt ausschließlich den Sammel-Endpunkt GET /tracks (50 IDs pro Request).
    Die Track-Objekte enthalten auch Artist- und Album-Namen, damit werden
    Umbenennungen von Artists/Alben ohne zusätzliche Requests erkannt.

    - rolling_sync(): prüft jede Nacht den Anteil mit dem ältesten checked_at,
      sodass der ganze Katalog in ROLLING_DAYS Tagen einmal geprüft ist
      (~28k Songs / 7 Tage -> ~80 Requests pro Nacht)
    - full_sync(): alles auf einmal (ehemals /db/update/all), ~10 Minuten
"""
import logging
import math
import os
import threading
import time

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from sqlalchemy import text, bindparam

from common.catalog.relations import rebuild_relations
from common.catalog.upsert import apply_tracks, log_changes
from common.config.config import CLIENT_ID, CLIENT_SECRET
from common.db.engine import engine

MARKET = os.getenv("SPOTIFY_MARKET", "DE")
ROLLING_DAYS = int(os.getenv("CATALOG_ROLLING_DAYS", "7"))
BATCH_SIZE = 50
PAUSE_SEC = 0.2  # zwischen Requests; 429 + Retry-After behandelt spotipy selbst

_sync_lock = threading.Lock()


def _client() -> spotipy.Spotify:
    # Client-Credentials reichen für Katalogdaten und schonen das User-Token
    return spotipy.Spotify(auth_manager=SpotifyClientCredentials(CLIENT_ID, CLIENT_SECRET),
                           retries=10, status_retries=10, backoff_factor=1.0, requests_timeout=20)


def _chunks(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def _mark_checked(conn, rows: list[dict], source: str):
    if not rows:
        return
    stmt = text("SELECT song_id, available, relinked_to FROM songs WHERE song_id IN :ids") \
        .bindparams(bindparam("ids", expanding=True))
    old = {r[0]: r for r in conn.execute(stmt, {"ids": [r["id"] for r in rows]})}
    changes = []
    for r in rows:
        prev = old.get(r["id"])
        if prev is None:
            continue
        if prev[2] != r["relinked_to"] and r["relinked_to"]:
            changes.append({"entity": "song", "entity_id": r["id"], "field": "relinked_to",
                            "old_value": prev[2], "new_value": r["relinked_to"], "source": source})
        if prev[1] is not None and prev[1] != r["available"]:
            changes.append({"entity": "song", "entity_id": r["id"], "field": "available",
                            "old_value": prev[1], "new_value": r["available"], "source": source})
    conn.execute(text("""
        UPDATE songs SET available = :available, relinked_to = :relinked_to, checked_at = NOW()
        WHERE song_id = :id
    """), rows)
    log_changes(conn, changes)


def _existing_ids(conn, ids) -> set:
    if not ids:
        return set()
    stmt = text("SELECT song_id FROM songs WHERE song_id IN :ids").bindparams(bindparam("ids", expanding=True))
    return {r[0] for r in conn.execute(stmt, {"ids": list(ids)})}


_batch_supported = True


def _get_tracks(sp: spotipy.Spotify, ids: list[str], market: str = None) -> list:
    """
    GET /tracks?ids=... (50 pro Request). Seit den Dev-Mode-Änderungen vom Februar 2026
    ist der Sammel-Endpunkt für Development-Mode-Apps gesperrt; dann wird auf
    GET /tracks/{id} pro Song ausgewichen (langsamer, aber funktionsfähig).
    """
    global _batch_supported
    if _batch_supported:
        try:
            return sp.tracks(ids, market=market)["tracks"]
        except spotipy.SpotifyException as e:
            if e.http_status not in (403, 404, 410):
                raise
            logging.warning(f"GET /tracks (Sammelabruf) nicht verfügbar ({e.http_status}), frage einzeln ab.")
            _batch_supported = False
    out = []
    for i in ids:
        try:
            out.append(sp.track(i, market=market))
        except spotipy.SpotifyException as e:
            if e.http_status not in (400, 404):
                raise
            out.append(None)
        time.sleep(PAUSE_SEC)
    return out


def sync_songs(song_ids: list[str], source: str = "sync", sp: spotipy.Spotify = None) -> dict:
    sp = sp or _client()
    stats = {"checked": 0, "relinked": 0, "unavailable": 0, "new_targets": 0, "changes": 0}
    for batch in _chunks(list(song_ids), BATCH_SIZE):
        res = _get_tracks(sp, batch, market=MARKET)
        own_tracks, checked, relinked_old, targets = [], [], [], set()
        for sid, t in zip(batch, res):
            if t is None:
                checked.append({"id": sid, "available": 0, "relinked_to": None})
                continue
            # Relinking: mit market liefert Spotify die abspielbare Ersatz-ID. linked_from fehlt
            # bei Dev-Mode-Apps seit 2026 -> die abweichende ID allein ist das Signal.
            if t.get("id") and t["id"] != sid:
                # Spotify spielt statt dieser ID eine andere ab -> Release wurde ersetzt
                checked.append({"id": sid, "available": 0, "relinked_to": t["id"]})
                relinked_old.append(sid)
                targets.add(t["id"])
            else:
                own_tracks.append(t)
                checked.append({"id": sid, "available": 1 if t.get("is_playable", True) else 0, "relinked_to": None})
        time.sleep(PAUSE_SEC)

        if relinked_old:
            # Ohne market liefert die API die eigenen Metadaten der alten ID (Titel, ISRC, Album)
            own_tracks += [t for t in _get_tracks(sp, relinked_old) if t]
            time.sleep(PAUSE_SEC)

        with engine.connect() as conn:
            missing_targets = sorted(targets - _existing_ids(conn, targets))
        if missing_targets:
            # Neue Versionen anlegen, damit sie als kanonische Version dienen können
            for t in _get_tracks(sp, missing_targets, market=MARKET):
                if t and t.get("id") in targets:
                    own_tracks.append(t)
                    checked.append({"id": t["id"], "available": 1 if t.get("is_playable", True) else 0,
                                    "relinked_to": None})
            stats["new_targets"] += len(missing_targets)
            time.sleep(PAUSE_SEC)

        with engine.begin() as conn:
            result = apply_tracks(conn, own_tracks, source)
            _mark_checked(conn, checked, source)
        stats["checked"] += len(batch)
        stats["relinked"] += len(relinked_old)
        stats["unavailable"] += sum(1 for c in checked if c["available"] == 0 and not c["relinked_to"])
        stats["changes"] += result["changes"]
    return stats


def _set_state(name: str, value: str):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO sync_state (name, value) VALUES (:name, :value)
            ON DUPLICATE KEY UPDATE value = VALUES(value)
        """), {"name": name, "value": value})


def _run(ids: list[str], state_name: str) -> dict:
    if not _sync_lock.acquire(blocking=False):
        logging.info("Katalog-Abgleich läuft bereits, überspringe.")
        return {"skipped": True}
    try:
        started = time.time()
        _set_state(f"{state_name}_status", f"running ({len(ids)} Songs)")
        stats = sync_songs(ids)
        with engine.begin() as conn:
            stats["relations"] = rebuild_relations(conn)
        _set_state(f"{state_name}_status", f"ok: {stats['checked']} Songs, {stats['changes']} Änderungen, "
                                           f"{time.time() - started:.0f}s")
        logging.info(f"Katalog-Abgleich ({state_name}) fertig: {stats}")
        return stats
    except Exception as e:
        _set_state(f"{state_name}_status", f"Fehler: {e}"[:200])
        raise
    finally:
        _sync_lock.release()


def rolling_sync() -> dict:
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM songs")).scalar()
        limit = math.ceil(total / ROLLING_DAYS)
        ids = [r[0] for r in conn.execute(text("""
            SELECT song_id FROM songs ORDER BY checked_at IS NOT NULL, checked_at LIMIT :limit
        """), {"limit": limit})]
    return _run(ids, "catalog_rolling")


def full_sync() -> dict:
    with engine.connect() as conn:
        ids = [r[0] for r in conn.execute(text("SELECT song_id FROM songs ORDER BY song_id"))]
    return _run(ids, "catalog_full")


def full_sync_in_background() -> bool:
    if _sync_lock.locked():
        return False
    threading.Thread(target=full_sync, name="catalog-full-sync", daemon=True).start()
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from common.db import migrate
    migrate.upgrade()
    print(full_sync())
