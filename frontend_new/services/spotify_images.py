from typing import Dict

from auth.spotify_auth_manager import SpotifyServerAuth
from frontend_new.core.extensions import cache

PLACEHOLDER = "https://vectorified.com/images/no-profile-picture-icon-21.jpg"

def _chunks(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i+size]


def spotify_client():
    auth = SpotifyServerAuth()
    # Ohne gespeichertes Token würde spotipy per input() nach der Redirect-URL fragen
    # und den Request-Thread dauerhaft blockieren -> lieber sauber abbrechen.
    if not auth.oauth.get_cached_token():
        raise RuntimeError("Die Verbindung zu Spotify fehlt noch. Bitte melde dich einmal über das Backend an.")
    return auth.get_authenticated_spotify_client()


def library_write_allowed() -> bool:
    # Darf die App Lieblingssongs ändern? (Scope der gespeicherten Spotify-Anmeldung)
    try:
        token = SpotifyServerAuth().oauth.get_cached_token() or {}
    except Exception:
        return False
    return "user-library-modify" in (token.get("scope") or "").split()


def images_or_empty(fetch, ids) -> Dict[str, str]:
    # Bilder sind optional: Fehler nicht cachen (memoize speichert nur Erfolge), Seite ohne Bilder rendern
    try:
        return fetch(tuple(ids))
    except Exception as e:
        print(f"Spotify-Bilder nicht verfügbar: {e}")
        return {}


@cache.memoize(timeout=86400)  # 24h
def track_images(ids_tuple: tuple) -> Dict[str, str]:
    ids = list(dict.fromkeys([i for i in ids_tuple if i]))  # unique, keep order
    if not ids: return {}
    out = {}
    sp = spotify_client()
    for batch in _chunks(ids, 50):
        res = sp.tracks(batch)
        for tr in res.get("tracks", []):
            out[tr["id"]] = (tr.get("album", {}).get("images") or [{}])[0].get("url", PLACEHOLDER)
    return out


@cache.memoize(timeout=86400)
def artist_images(ids_tuple: tuple) -> Dict[str, str]:
    ids = list(dict.fromkeys([i for i in ids_tuple if i]))
    if not ids: return {}
    out = {}
    sp = spotify_client()
    for batch in _chunks(ids, 50):
        res = sp.artists(batch)
        for ar in res.get("artists", []):
            out[ar["id"]] = (ar.get("images") or [{}])[0].get("url", PLACEHOLDER)
    return out

@cache.memoize(timeout=86400)
def album_images(ids_tuple: tuple) -> Dict[str, str]:
    ids = list(dict.fromkeys([i for i in ids_tuple if i]))
    if not ids: return {}
    out = {}
    sp = spotify_client()
    for batch in _chunks(ids, 20):
        res = sp.albums(batch)
        for al in res.get("albums", []):
            out[al["id"]] = (al.get("images") or [{}])[0].get("url", PLACEHOLDER)
    return out
