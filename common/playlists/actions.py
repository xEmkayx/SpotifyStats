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
import time
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
        raise PlaylistActionError("Diese Playlist gibt es hier nicht.")
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
        raise PlaylistActionError("In dieser Playlist sind lokale Dateien. Die kann Spotify von außen nicht "
                                  "wieder einfügen, deshalb bitte direkt in der Spotify-App bearbeiten.")


def _check_unchanged(expected_hash: str, items: list[dict], meta: dict):
    if expected_hash and history.content_hash(items, meta.get("name"), meta.get("description")) != expected_hash:
        raise PlaylistActionError("Die Playlist hat sich in der Zwischenzeit geändert. Lade die Seite neu und "
                                  "schau dir die Vorschau noch einmal an.")


# --- Vorschau ---

def preview_restore(snapshot_pk: int) -> dict:
    with engine.connect() as conn:
        snap = conn.execute(text("SELECT * FROM playlist_snapshots WHERE id = :s"), {"s": snapshot_pk}).mappings().first()
        if not snap:
            raise PlaylistActionError("Diesen Stand gibt es nicht mehr.")
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
            raise PlaylistActionError("Diesen Stand gibt es nicht mehr.")
        row = _playlist_row(conn, snap["playlist_id"])
        target = history.snapshot_items(conn, snapshot_pk)
    if row["playlist_id"] == history.LIKED_ID:
        raise PlaylistActionError("Lieblingssongs lassen sich nicht zurücksetzen, weil Spotify sie immer nach "
                                  "dem Datum sortiert, an dem du sie gespeichert hast.")
    uris = [it["uri"] for it in target if it["uri"] and not it["is_local"]]

    if row["deleted_at"]:
        # Gelöschte Playlist: als neue Playlist anlegen
        created = api.create_playlist(sp, f"{snap['name'] or row['name']} (wiederhergestellt)", public=False,
                                      description=snap["description"] or "")
        api.replace_playlist_items(sp, created["id"], uris)
        history.sync_playlist(sp, {**created, "owner": created.get("owner") or {"id": row["owner_id"]}},
                              reason="restore", force_fetch=True)
        return f"Fertig – die Playlist ist als „{created.get('name')}“ wieder da ({len(uris)} Songs)."

    meta, items, _ = _backup_current(sp, row["playlist_id"], "before_restore")
    _check_unchanged(expected_hash, items, meta)
    _check_writable(items)
    api.replace_playlist_items(sp, row["playlist_id"], uris)
    history.sync_playlist(sp, {**meta, "id": row["playlist_id"]}, reason="restore", force_fetch=True)
    taken = snap["taken_at"].replace(tzinfo=timezone.utc).astimezone(_DISPLAY_TZ)
    return f"Fertig – die Playlist ist wieder auf dem Stand vom {taken:%d.%m.%Y, %H:%M} Uhr ({len(uris)} Songs)."


def _selected(todo: list[dict], positions) -> list[dict]:
    # positions=None -> alle; sonst nur die ausgewählten Plätze
    return todo if positions is None else [it for it in todo if it["position"] in set(positions)]


def replace_superseded(sp, playlist_id: str, expected_hash: str, positions=None) -> str:
    if playlist_id == history.LIKED_ID:
        return _replace_superseded_liked(sp, expected_hash, positions)
    meta, items, _ = _backup_current(sp, playlist_id, "before_replace")
    _check_unchanged(expected_hash, items, meta)
    todo, _ = superseded_items(playlist_id)
    todo = _selected(todo, positions)
    if not todo:
        return "In dieser Playlist ist schon alles aktuell."
    if any(it["is_local"] for it in items):
        replaced = _replace_in_place(sp, playlist_id, items, todo)
    else:
        new_uri = {it["position"]: it["new_uri"] for it in todo}
        api.replace_playlist_items(sp, playlist_id, [new_uri.get(it["position"], it["uri"]) for it in items])
        replaced = len(todo)
    history.sync_playlist(sp, {**meta, "id": playlist_id}, reason="replace", force_fetch=True)
    songs = "1 Song ist" if replaced == 1 else f"{replaced} Songs sind"
    return f"Fertig – {songs} jetzt in der aktuellen Version drin, an derselben Stelle wie vorher."


def _replace_in_place(sp, playlist_id: str, items: list[dict], todo: list[dict]) -> int:
    """
    Für Playlists mit lokalen Dateien: die neue Version direkt vor der alten einfügen und danach die
    alten URIs entfernen. Lokale Dateien werden nie angefasst, die Reihenfolge bleibt exakt erhalten.
    """
    selected_uris = {it["uri"] for it in todo}
    # Entfernen trifft alle Vorkommen einer URI -> nur URIs tauschen, deren Vorkommen alle ausgewählt sind
    all_positions = {}
    for it in items:
        all_positions.setdefault(it["uri"], set()).add(it["position"])
    todo = [it for it in todo if all_positions.get(it["uri"], set()) <= {t["position"] for t in todo
                                                                          if t["uri"] == it["uri"]}]
    # Von hinten nach vorne einfügen, damit sich die Positionen davor nicht verschieben
    for it in sorted(todo, key=lambda t: t["position"], reverse=True):
        api.insert_item(sp, playlist_id, it["new_uri"], it["position"])
        time.sleep(0.1)  # ein Request pro Song -> Rate Limit schonen
    api.remove_items(sp, playlist_id, sorted({it["uri"] for it in todo} & selected_uris))
    return len(todo)


def can_modify_library(sp) -> bool:
    return "user-library-modify" in api.token_scopes(sp.auth_manager)


def _replace_superseded_liked(sp, expected_hash: str, positions=None) -> str:
    if not can_modify_library(sp):
        raise PlaylistActionError("Für deine Lieblingssongs fehlt noch eine Berechtigung bei Spotify "
                                  "(„user-library-modify“). Dafür musst du die Verbindung zu Spotify einmal neu "
                                  "herstellen.")
    total, items = api.get_saved_tracks(sp)
    with engine.connect() as conn:
        latest = history.latest_snapshot(conn, history.LIKED_ID)
    if expected_hash and latest and latest["content_hash"] != expected_hash:
        raise PlaylistActionError("Deine Lieblingssongs haben sich in der Zwischenzeit geändert. Lade die Seite "
                                  "neu und schau dir die Vorschau noch einmal an.")
    todo, _ = superseded_items(history.LIKED_ID)
    todo = _selected(todo, positions)
    if not todo:
        return "Bei deinen Lieblingssongs ist schon alles aktuell."
    api.save_to_library(sp, [it["new_uri"] for it in todo])
    api.remove_from_library(sp, [it["uri"] for it in todo])
    history.sync_liked(sp, reason="replace", force_fetch=True)
    songs = "1 Lieblingssong ist" if len(todo) == 1 else f"{len(todo)} Lieblingssongs sind"
    return f"Fertig – {songs} jetzt in der aktuellen Version drin und stehen ganz oben."
