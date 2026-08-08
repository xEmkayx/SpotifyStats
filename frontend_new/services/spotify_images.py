from typing import Dict

from auth.spotify_auth_manager import SpotifyServerAuth
from frontend_new.core.extensions import cache

PLACEHOLDER = "https://vectorified.com/images/no-profile-picture-icon-21.jpg"

def _chunks(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i+size]


def _sp():
    auth = SpotifyServerAuth()
    return auth.get_authenticated_spotify_client()


@cache.memoize(timeout=86400)  # 24h
def track_images(ids_tuple: tuple) -> Dict[str, str]:
    ids = list(dict.fromkeys([i for i in ids_tuple if i]))  # unique, keep order
    if not ids: return {}
    out = {}
    sp = _sp()
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
    sp = _sp()
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
    sp = _sp()
    for batch in _chunks(ids, 20):
        res = sp.albums(batch)
        for al in res.get("albums", []):
            out[al["id"]] = (al.get("images") or [{}])[0].get("url", PLACEHOLDER)
    return out
