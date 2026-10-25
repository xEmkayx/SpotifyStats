"""
    Playlist- und Bibliotheks-Zugriffe auf die Spotify Web API.

    Seit den Dev-Mode-Änderungen (Februar 2026) heißen die Playlist-Routen
    /playlists/{id}/items (statt /tracks) und das Feld pro Eintrag "item"
    (statt "track"); "Playlist für User anlegen" läuft über POST /me/playlists,
    Speichern in der Bibliothek über PUT/DELETE /me/library.
    Hier wird jeweils zuerst der neue Weg versucht und bei 403/404/410 auf den
    alten ausgewichen (Apps im Extended Quota Mode nutzen weiter die alten).
"""
import logging
import time

import spotipy

MARKET_DEFAULT = "DE"
_FALLBACK_STATUS = (403, 404, 410)
_use_items_route = True


def _call_with_fallback(new, old):
    global _use_items_route
    if _use_items_route:
        try:
            return new()
        except spotipy.SpotifyException as e:
            if e.http_status not in _FALLBACK_STATUS:
                raise
            logging.warning(f"Neue Playlist-Route nicht verfügbar ({e.http_status}), nutze /tracks.")
            _use_items_route = False
    return old()


def _write(call, max_attempts: int = 6):
    """
    Schreibende Anfrage, die bei Rate Limit (429) immer zu Ende geführt wird: wartet die von Spotify
    genannte Zeit und versucht es erneut. Würde stattdessen abgebrochen, bliebe eine Playlist halb
    geschrieben zurück (z. B. nur die ersten 100 Songs nach dem Ersetzen).
    """
    for attempt in range(1, max_attempts + 1):
        try:
            return call()
        except spotipy.SpotifyException as e:
            if e.http_status != 429 or attempt == max_attempts:
                raise
            try:
                wait = int((e.headers or {}).get("Retry-After", 30))
            except (TypeError, ValueError):
                wait = 30
            logging.warning(f"Spotify bremst beim Schreiben, warte {wait} s und versuche es erneut")
            time.sleep(min(wait, 1800) + 1)


def current_user_id(sp: spotipy.Spotify) -> str:
    return sp.current_user()["id"]


def iter_my_playlists(sp: spotipy.Spotify):
    # GET /me/playlists: gefolgte + eigene Playlists; gefiltert wird beim Aufrufer
    page = sp.current_user_playlists(limit=50)
    while page:
        yield from page.get("items") or []
        page = sp.next(page) if page.get("next") else None


def _entry_object(entry: dict) -> dict:
    return entry.get("item") or entry.get("track") or {}


def get_playlist_items(sp: spotipy.Spotify, playlist_id: str, market: str = MARKET_DEFAULT) -> list[dict]:
    """
    Alle Einträge einer Playlist in Reihenfolge, normalisiert:
    {position, uri, track_id, playable_id, name, artists, album, duration_ms, added_at, added_by, is_local}
    track_id ist die ID, die tatsächlich in der Playlist steht; playable_id die von Spotify
    für den Markt abgespielte (weicht bei ersetzten Releases ab).
    """
    params = {"limit": 100, "market": market, "additional_types": "track,episode"}
    page = _call_with_fallback(
        lambda: sp._get(f"playlists/{playlist_id}/items", **params),
        lambda: sp._get(f"playlists/{playlist_id}/tracks", **params),
    )
    entries = []
    while page:
        entries += page.get("items") or []
        page = sp.next(page) if page.get("next") else None
    return [normalize_entry(e, pos) for pos, e in enumerate(entries)]


def normalize_entry(entry: dict, position: int) -> dict:
    obj = _entry_object(entry)
    linked_from = obj.get("linked_from") or {}
    is_local = bool(entry.get("is_local") or obj.get("is_local"))
    playable_id = obj.get("id")
    track_id = linked_from.get("id") or playable_id
    uri = linked_from.get("uri") or obj.get("uri")
    artists = obj.get("artists") or (obj.get("show") and [{"name": obj["show"].get("name")}]) or []
    return {
        "position": position,
        "uri": uri,
        "track_id": track_id,
        "playable_id": playable_id if playable_id != track_id else None,
        "name": obj.get("name"),
        "artists": ", ".join(a.get("name") or "" for a in artists),
        "album": (obj.get("album") or {}).get("name"),
        "duration_ms": obj.get("duration_ms"),
        "added_at": entry.get("added_at"),
        "added_by": (entry.get("added_by") or {}).get("id"),
        "is_local": is_local,
    }


def iter_saved_track_pages(sp: spotipy.Spotify, market: str = MARKET_DEFAULT):
    """GET /me/tracks seitenweise (neueste zuerst): liefert (total, [normalisierte Einträge]) je Seite."""
    page = sp.current_user_saved_tracks(limit=50, market=market)
    offset = 0
    while page:
        entries = page.get("items") or []
        yield page.get("total") or 0, [normalize_entry(e, offset + pos) for pos, e in enumerate(entries)]
        offset += len(entries)
        page = sp.next(page) if page.get("next") else None


def get_saved_tracks(sp: spotipy.Spotify, market: str = MARKET_DEFAULT, limit_pages: int = None) -> tuple[int, list]:
    total, items = 0, []
    for n, (total, page_items) in enumerate(iter_saved_track_pages(sp, market), start=1):
        items += page_items
        if limit_pages and n >= limit_pages:
            break
    return total, items


def replace_playlist_items(sp: spotipy.Spotify, playlist_id: str, uris: list[str]) -> str:
    """Überschreibt die Playlist mit genau dieser Reihenfolge. Gibt die neue snapshot_id zurück."""
    first, rest = uris[:100], uris[100:]
    res = _write(lambda: _call_with_fallback(
        lambda: sp._put(f"playlists/{playlist_id}/items", payload={"uris": first}),
        lambda: sp._put(f"playlists/{playlist_id}/tracks", payload={"uris": first}),
    ))
    for i in range(0, len(rest), 100):
        chunk = rest[i:i + 100]
        res = _write(lambda: _call_with_fallback(
            lambda: sp._post(f"playlists/{playlist_id}/items", payload={"uris": chunk}),
            lambda: sp._post(f"playlists/{playlist_id}/tracks", payload={"uris": chunk}),
        ))
    return (res or {}).get("snapshot_id")


def insert_item(sp: spotipy.Spotify, playlist_id: str, uri: str, position: int) -> str:
    """Fügt einen Eintrag an genau dieser Position ein (der bisherige rutscht eins nach hinten)."""
    payload = {"uris": [uri], "position": position}
    res = _write(lambda: _call_with_fallback(
        lambda: sp._post(f"playlists/{playlist_id}/items", payload=payload),
        lambda: sp._post(f"playlists/{playlist_id}/tracks", payload=payload),
    ))
    return (res or {}).get("snapshot_id")


def remove_items(sp: spotipy.Spotify, playlist_id: str, uris: list[str]) -> str:
    """Entfernt alle Vorkommen der URIs (lokale Dateien bleiben unberührt)."""
    res = None
    for i in range(0, len(uris), 100):
        objs = [{"uri": u} for u in uris[i:i + 100]]

        def new_route():
            try:
                return sp._delete(f"playlists/{playlist_id}/items", payload={"items": objs})
            except spotipy.SpotifyException as e:
                if e.http_status != 400:
                    raise
                # Falls die neue Route noch den alten Feldnamen erwartet
                return sp._delete(f"playlists/{playlist_id}/items", payload={"tracks": objs})

        res = _write(lambda: _call_with_fallback(
            new_route,
            lambda: sp._delete(f"playlists/{playlist_id}/tracks", payload={"tracks": objs}),
        ))
    return (res or {}).get("snapshot_id")


def create_playlist(sp: spotipy.Spotify, name: str, public: bool = False, description: str = "") -> dict:
    payload = {"name": name, "public": public, "description": description}
    try:
        return sp._post("me/playlists", payload=payload)
    except spotipy.SpotifyException as e:
        if e.http_status not in _FALLBACK_STATUS:
            raise
        return sp.user_playlist_create(current_user_id(sp), name, public=public, description=description)


def token_scopes(auth_manager) -> set:
    token = auth_manager.get_cached_token() or {}
    return set((token.get("scope") or "").split())


def save_to_library(sp: spotipy.Spotify, uris: list[str]):
    for i in range(0, len(uris), 40):
        chunk = uris[i:i + 40]
        def save(chunk=chunk):
            try:
                sp._put("me/library", args=None, payload=None, uris=",".join(chunk))
            except spotipy.SpotifyException as e:
                if e.http_status not in _FALLBACK_STATUS:
                    raise
                sp.current_user_saved_tracks_add([u.split(":")[-1] for u in chunk])
        _write(save)


def remove_from_library(sp: spotipy.Spotify, uris: list[str]):
    for i in range(0, len(uris), 40):
        chunk = uris[i:i + 40]
        def remove(chunk=chunk):
            try:
                sp._delete("me/library", args=None, payload=None, uris=",".join(chunk))
            except spotipy.SpotifyException as e:
                if e.http_status not in _FALLBACK_STATUS:
                    raise
                sp.current_user_saved_tracks_delete([u.split(":")[-1] for u in chunk])
        _write(remove)
