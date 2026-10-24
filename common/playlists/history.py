"""
    Playlist-Verlauf: speichert den Inhalt eigener Playlists und der Lieblingssongs
    als Snapshots und berechnet Unterschiede zwischen zwei Ständen.

    Die Spotify-snapshot_id dient nur zur billigen Änderungserkennung (GET /me/playlists
    liefert sie für alle Playlists auf einmal); die eigentliche Historie sind die
    hier gespeicherten Track-Listen.
"""
import difflib
import hashlib
import logging
from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import text

from common.db.engine import engine
from common.spotify import playlist_api as api

LIKED_ID = "liked"
LIKED_NAME = "Lieblingssongs"
_LOCK_NAME = "spotify_stats_playlist_sync"


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_spotify_time(value):
    # "2024-05-01T12:34:56Z" -> naive UTC
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
    except ValueError:
        return None


def content_hash(items: list[dict], name: str, description: str) -> str:
    h = hashlib.sha1()
    h.update(f"{name or ''}\x00{description or ''}\x00".encode())
    for it in items:
        h.update(f"{it.get('uri') or ''}\n".encode())
    return h.hexdigest()


@contextmanager
def sync_lock(timeout: int = 0):
    # Serialisiert Syncs über Prozesse hinweg (Backend-Scheduler + "Jetzt synchronisieren" im Frontend)
    with engine.connect() as conn:
        got = conn.execute(text("SELECT GET_LOCK(:n, :t)"), {"n": _LOCK_NAME, "t": timeout}).scalar()
        try:
            yield bool(got)
        finally:
            if got:
                conn.execute(text("SELECT RELEASE_LOCK(:n)"), {"n": _LOCK_NAME})


def latest_snapshot(conn, playlist_id: str):
    return conn.execute(text("""
        SELECT id, content_hash, spotify_snapshot_id, track_count, taken_at
        FROM playlist_snapshots WHERE playlist_id = :p ORDER BY id DESC LIMIT 1
    """), {"p": playlist_id}).mappings().first()


def snapshot_items(conn, snapshot_pk: int) -> list[dict]:
    return [dict(r) for r in conn.execute(text("""
        SELECT position, uri, track_id, playable_id, name, artists, album, duration_ms, added_at, added_by, is_local
        FROM playlist_snapshot_items WHERE snapshot_id = :s ORDER BY position
    """), {"s": snapshot_pk}).mappings()]


def store_snapshot(conn, playlist_id: str, items: list[dict], name: str, description: str,
                   spotify_snapshot_id: str, reason: str, force: bool = False):
    """Legt einen Snapshot an, wenn sich etwas geändert hat (oder force). Gibt die ID oder None zurück."""
    digest = content_hash(items, name, description)
    latest = latest_snapshot(conn, playlist_id)
    if latest and latest["content_hash"] == digest and not force:
        return None
    now = utcnow()
    snap_pk = conn.execute(text("""
        INSERT INTO playlist_snapshots (playlist_id, spotify_snapshot_id, name, description, track_count,
                                        content_hash, reason, taken_at)
        VALUES (:p, :sid, :name, :desc, :count, :hash, :reason, :now)
    """), {"p": playlist_id, "sid": spotify_snapshot_id, "name": name, "desc": description or "",
           "count": len(items), "hash": digest, "reason": reason, "now": now}).lastrowid
    if items:
        conn.execute(text("""
            INSERT INTO playlist_snapshot_items (snapshot_id, position, uri, track_id, playable_id, name, artists,
                                                 album, duration_ms, added_at, added_by, is_local)
            VALUES (:s, :position, :uri, :track_id, :playable_id, :name, :artists, :album, :duration_ms,
                    :added_at, :added_by, :is_local)
        """), [{**it, "s": snap_pk, "added_at": parse_spotify_time(it.get("added_at")),
                "is_local": int(bool(it.get("is_local")))}
               for it in items])
    conn.execute(text("UPDATE playlists SET last_changed_at = :now WHERE playlist_id = :p"),
                 {"now": now, "p": playlist_id})
    return snap_pk


def _upsert_playlist(conn, playlist_id: str, meta: dict):
    now = utcnow()
    conn.execute(text("""
        INSERT INTO playlists (playlist_id, name, description, owner_id, is_public, collaborative, image_url,
                               spotify_snapshot_id, track_count, first_seen_at, last_synced_at, deleted_at)
        VALUES (:id, :name, :description, :owner_id, :is_public, :collaborative, :image_url,
                :snapshot_id, :track_count, :now, :now, NULL)
        ON DUPLICATE KEY UPDATE name = VALUES(name), description = VALUES(description),
            owner_id = VALUES(owner_id), is_public = VALUES(is_public), collaborative = VALUES(collaborative),
            image_url = VALUES(image_url), spotify_snapshot_id = VALUES(spotify_snapshot_id),
            track_count = VALUES(track_count), last_synced_at = VALUES(last_synced_at), deleted_at = NULL
    """), {"id": playlist_id, "now": now, **meta})


def _playlist_meta(p: dict) -> dict:
    items_info = p.get("items") if isinstance(p.get("items"), dict) else p.get("tracks") or {}
    images = p.get("images") or []
    return {
        "name": p.get("name"),
        "description": p.get("description") or "",
        "owner_id": (p.get("owner") or {}).get("id"),
        "is_public": None if p.get("public") is None else int(bool(p.get("public"))),
        "collaborative": int(bool(p.get("collaborative"))),
        "image_url": images[0].get("url") if images else None,
        "snapshot_id": p.get("snapshot_id"),
        "track_count": items_info.get("total"),
    }


def sync_playlist(sp, playlist: dict, reason: str = "sync", force_fetch: bool = False) -> bool:
    """Synchronisiert eine Playlist (Spotify-Objekt aus /me/playlists). True, wenn ein Snapshot entstand."""
    pid = playlist["id"]
    meta = _playlist_meta(playlist)
    with engine.connect() as conn:
        stored = conn.execute(text("SELECT spotify_snapshot_id FROM playlists WHERE playlist_id = :p"),
                              {"p": pid}).scalar()
        has_snapshot = latest_snapshot(conn, pid) is not None
    changed = force_fetch or not has_snapshot or stored != meta["snapshot_id"]
    with engine.begin() as conn:
        _upsert_playlist(conn, pid, meta)
    if not changed:
        return False
    items = api.get_playlist_items(sp, pid)
    with engine.begin() as conn:
        snap = store_snapshot(conn, pid, items, meta["name"], meta["description"], meta["snapshot_id"],
                              "initial" if not has_snapshot else reason)
    return snap is not None


def sync_playlist_by_id(sp, playlist_id: str, reason: str = "manual") -> bool:
    if playlist_id == LIKED_ID:
        return sync_liked(sp, reason=reason, force_fetch=True)
    meta = sp.playlist(playlist_id, fields="id,name,description,snapshot_id,public,collaborative,owner,images")
    return sync_playlist(sp, meta, reason=reason, force_fetch=True)


def sync_liked(sp, reason: str = "sync", force_fetch: bool = False) -> bool:
    # Für Lieblingssongs gibt es keine snapshot_id: Gesamtzahl + erste Seite als Änderungssignal
    total, first_page = api.get_saved_tracks(sp, limit_pages=1)
    with engine.connect() as conn:
        latest = latest_snapshot(conn, LIKED_ID)
        latest_head = [it["uri"] for it in snapshot_items(conn, latest["id"])[:len(first_page)]] if latest else []
    unchanged = latest and latest["track_count"] == total and latest_head == [it["uri"] for it in first_page]
    meta = {"name": LIKED_NAME, "description": "", "owner_id": None, "is_public": 0, "collaborative": 0,
            "image_url": None, "snapshot_id": None, "track_count": total}
    with engine.begin() as conn:
        _upsert_playlist(conn, LIKED_ID, meta)
    if unchanged and not force_fetch:
        return False
    _, items = api.get_saved_tracks(sp)
    with engine.begin() as conn:
        snap = store_snapshot(conn, LIKED_ID, items, LIKED_NAME, "", None, "initial" if not latest else reason)
    return snap is not None


def sync_all(sp, include_liked: bool = True) -> dict:
    """Alle eigenen Playlists (owner = aktueller User) und die Lieblingssongs."""
    stats = {"playlists": 0, "changed": 0, "deleted": 0, "liked_changed": False, "skipped": False}
    with sync_lock() as got:
        if not got:
            stats["skipped"] = True
            return stats
        me = api.current_user_id(sp)
        seen = set()
        for p in api.iter_my_playlists(sp):
            if not p or (p.get("owner") or {}).get("id") != me:
                continue  # von Spotify generiert oder von anderen Usern -> nicht verfolgen
            seen.add(p["id"])
            stats["playlists"] += 1
            try:
                stats["changed"] += int(sync_playlist(sp, p))
            except Exception:
                logging.exception(f"Playlist {p.get('id')} konnte nicht synchronisiert werden")
        with engine.begin() as conn:
            known = [r[0] for r in conn.execute(text(
                "SELECT playlist_id FROM playlists WHERE deleted_at IS NULL AND playlist_id <> :liked"),
                {"liked": LIKED_ID})]
            gone = [pid for pid in known if pid not in seen]
            for pid in gone:
                conn.execute(text("UPDATE playlists SET deleted_at = :now WHERE playlist_id = :p"),
                             {"now": utcnow(), "p": pid})
            stats["deleted"] = len(gone)
        if include_liked:
            stats["liked_changed"] = sync_liked(sp)
    logging.info(f"Playlist-Sync: {stats}")
    return stats


def diff_items(old: list[dict], new: list[dict]) -> list[dict]:
    """
    Unterschiede zwischen zwei Track-Listen wie bei git diff:
    added (+), removed (−), moved (↕, Position geändert), replaced (⇄, alte Version gegen neue getauscht).
    """
    a = [it["uri"] for it in old]
    b = [it["uri"] for it in new]
    removed, added = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag in ("delete", "replace"):
            removed += [old[i] for i in range(i1, i2)]
        if tag in ("insert", "replace"):
            added += [new[j] for j in range(j1, j2)]
    changes = []
    # Verschoben: gleiche URI entfernt und an anderer Stelle eingefügt
    for r in list(removed):
        match = next((x for x in added if x["uri"] == r["uri"]), None)
        if match:
            removed.remove(r)
            added.remove(match)
            changes.append({"op": "moved", "old": r, "new": match})
    # Version ersetzt: alte ID wird von Spotify auf die neue umgeleitet
    for r in list(removed):
        match = next((x for x in added if r.get("playable_id") and x.get("track_id") == r["playable_id"]), None)
        if match:
            removed.remove(r)
            added.remove(match)
            changes.append({"op": "replaced", "old": r, "new": match})
    changes += [{"op": "removed", "old": r, "new": None} for r in removed]
    changes += [{"op": "added", "old": None, "new": x} for x in added]
    order = {"replaced": 0, "removed": 1, "added": 2, "moved": 3}
    changes.sort(key=lambda c: (order[c["op"]], (c["new"] or c["old"])["position"]))
    return changes
