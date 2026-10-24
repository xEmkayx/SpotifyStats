"""
    Schreibende Playlist-Aktionen: auf einen Snapshot zurücksetzen, gelöschte Playlist
    wiederherstellen und ersetzte Versionen (Track-Relinking) austauschen.

    Sicherheitsnetz für alle Aktionen:
      1. aktuellen Stand frisch von Spotify laden und als Snapshot sichern
      2. prüfen, dass die Playlist seit der Vorschau nicht verändert wurde
         (Spotify-snapshot_id bzw. Inhalt) -> sonst Abbruch
      3. schreiben, danach erneut synchronisieren
    Positionen bleiben erhalten; added_at setzt Spotify beim Neuschreiben neu.
"""
import os
from datetime import timezone
from zoneinfo import ZoneInfo

from sqlalchemy import text

from common.db.engine import engine
from common.playlists import history
from common.spotify import playlist_api as api


_DISPLAY_TZ = ZoneInfo(os.getenv("DISPLAY_TZ", "Europe/Berlin"))


class PlaylistActionError(Exception):
    pass


def _playlist_row(conn, playlist_id: str):
    row = conn.execute(text("SELECT * FROM playlists WHERE playlist_id = :p"), {"p": playlist_id}).mappings().first()
    if not row:
        raise PlaylistActionError("Playlist unbekannt.")
    return row


def _current_state(sp, playlist_id: str) -> tuple[dict, list[dict]]:
    meta = sp.playlist(playlist_id, fields="id,name,description,snapshot_id,public,collaborative,owner,images")
    return meta, api.get_playlist_items(sp, playlist_id)


def _backup_current(sp, playlist_id: str, reason: str) -> tuple[dict, list[dict], int]:
    meta, items = _current_state(sp, playlist_id)
    with engine.begin() as conn:
        snap = history.store_snapshot(conn, playlist_id, items, meta.get("name"), meta.get("description"),
                                      meta.get("snapshot_id"), reason)
        snap = snap or history.latest_snapshot(conn, playlist_id)["id"]
    return meta, items, snap


def _check_writable(items: list[dict]):
    if any(it["is_local"] for it in items):
        # Lokale Dateien lassen sich über die API nicht wieder einfügen -> Neuschreiben würde sie löschen
        raise PlaylistActionError("Die Playlist enthält lokale Dateien; die lassen sich über die API nicht "
                                  "neu schreiben. Bitte in der Spotify-App bearbeiten.")


def _check_unchanged(expected_hash: str, items: list[dict], meta: dict):
    if expected_hash and history.content_hash(items, meta.get("name"), meta.get("description")) != expected_hash:
        raise PlaylistActionError("Die Playlist wurde seit der Vorschau verändert. Bitte neu laden und erneut prüfen.")


# --- Vorschau ---

def preview_restore(snapshot_pk: int) -> dict:
    with engine.connect() as conn:
        snap = conn.execute(text("SELECT * FROM playlist_snapshots WHERE id = :s"), {"s": snapshot_pk}).mappings().first()
        if not snap:
            raise PlaylistActionError("Snapshot unbekannt.")
        latest = history.latest_snapshot(conn, snap["playlist_id"])
        target = history.snapshot_items(conn, snapshot_pk)
        current = history.snapshot_items(conn, latest["id"])
    return {"playlist_id": snap["playlist_id"], "changes": history.diff_items(current, target),
            "expected_hash": latest["content_hash"], "local_files": sum(1 for it in target if it["is_local"])}


def superseded_items(playlist_id: str) -> tuple[list[dict], str]:
    """Einträge im letzten Snapshot, die Spotify auf eine neuere Version umleitet."""
    with engine.connect() as conn:
        latest = history.latest_snapshot(conn, playlist_id)
        if not latest:
            return [], None
        items = history.snapshot_items(conn, latest["id"])
        # Zusätzlich die Relinking-Information aus dem Katalog nutzen (z. B. für Lieblingssongs)
        relinked = dict(conn.execute(text("SELECT song_id, relinked_to FROM songs WHERE relinked_to IS NOT NULL")).all())
    out = []
    for it in items:
        new_id = it["playable_id"] or relinked.get(it["track_id"])
        if new_id and new_id != it["track_id"] and not it["is_local"]:
            out.append({**it, "new_id": new_id, "new_uri": f"spotify:track:{new_id}"})
    return out, latest["content_hash"]


# --- Ausführen ---

def restore_snapshot(sp, snapshot_pk: int, expected_hash: str) -> str:
    with engine.connect() as conn:
        snap = conn.execute(text("SELECT * FROM playlist_snapshots WHERE id = :s"), {"s": snapshot_pk}).mappings().first()
        if not snap:
            raise PlaylistActionError("Snapshot unbekannt.")
        row = _playlist_row(conn, snap["playlist_id"])
        target = history.snapshot_items(conn, snapshot_pk)
    if row["playlist_id"] == history.LIKED_ID:
        raise PlaylistActionError("Lieblingssongs können nicht zurückgesetzt werden (Spotify erlaubt keine Reihenfolge).")
    uris = [it["uri"] for it in target if it["uri"] and not it["is_local"]]

    if row["deleted_at"]:
        # Gelöschte Playlist: als neue Playlist anlegen
        created = api.create_playlist(sp, f"{snap['name'] or row['name']} (wiederhergestellt)", public=False,
                                      description=snap["description"] or "")
        api.replace_playlist_items(sp, created["id"], uris)
        history.sync_playlist(sp, {**created, "owner": created.get("owner") or {"id": row["owner_id"]}},
                              reason="restore", force_fetch=True)
        return f"Als neue Playlist „{created.get('name')}“ wiederhergestellt ({len(uris)} Titel)."

    meta, items, _ = _backup_current(sp, row["playlist_id"], "before_restore")
    _check_unchanged(expected_hash, items, meta)
    _check_writable(items)
    api.replace_playlist_items(sp, row["playlist_id"], uris)
    history.sync_playlist(sp, {**meta, "id": row["playlist_id"]}, reason="restore", force_fetch=True)
    taken = snap["taken_at"].replace(tzinfo=timezone.utc).astimezone(_DISPLAY_TZ)
    return f"Playlist auf den Stand vom {taken:%d.%m.%Y %H:%M} zurückgesetzt ({len(uris)} Titel)."


def replace_superseded(sp, playlist_id: str, expected_hash: str) -> str:
    if playlist_id == history.LIKED_ID:
        return _replace_superseded_liked(sp, expected_hash)
    meta, items, _ = _backup_current(sp, playlist_id, "before_replace")
    _check_unchanged(expected_hash, items, meta)
    _check_writable(items)
    todo, _ = superseded_items(playlist_id)
    if not todo:
        return "Keine ersetzten Versionen in dieser Playlist."
    new_uri = {it["position"]: it["new_uri"] for it in todo}
    uris = [new_uri.get(it["position"], it["uri"]) for it in items]
    api.replace_playlist_items(sp, playlist_id, uris)
    history.sync_playlist(sp, {**meta, "id": playlist_id}, reason="replace", force_fetch=True)
    return f"{len(todo)} Titel durch die aktuelle Version ersetzt (Positionen unverändert)."


def _replace_superseded_liked(sp, expected_hash: str) -> str:
    if "user-library-modify" not in api.token_scopes(sp.auth_manager):
        raise PlaylistActionError("Für Lieblingssongs fehlt die Berechtigung „user-library-modify“. "
                                  "Dafür muss die Spotify-Autorisierung mit erweitertem Scope erneuert werden.")
    total, items = api.get_saved_tracks(sp)
    with engine.connect() as conn:
        latest = history.latest_snapshot(conn, history.LIKED_ID)
    if expected_hash and latest and latest["content_hash"] != expected_hash:
        raise PlaylistActionError("Die Lieblingssongs wurden seit der Vorschau verändert. Bitte neu laden.")
    todo, _ = superseded_items(history.LIKED_ID)
    if not todo:
        return "Keine ersetzten Versionen in den Lieblingssongs."
    api.save_to_library(sp, [it["new_uri"] for it in todo])
    api.remove_from_library(sp, [it["uri"] for it in todo])
    history.sync_liked(sp, reason="replace", force_fetch=True)
    return f"{len(todo)} Lieblingssongs durch die aktuelle Version ersetzt (sie stehen jetzt oben in der Liste)."
