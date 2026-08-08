from datetime import date
from typing import Tuple, Optional

from auth import spotify_auth_manager
from auth.spotify_auth_manager import SpotifyServerAuth
from frontend_new.services.top_songs import top_song_ids


def _chunk(seq, size=100):
    for i in range(0, len(seq), size):
        yield seq[i:i+size]

def create_playlist_from_current_filters(
    start_date: str, end_date: str, metric: str, top_n: int, cache_version: int,
    playlist_name: Optional[str]=None, public: bool=True
    ) -> Tuple[bool, str, Optional[str]]:
    # 1) Daten holen
    start_dt = f"{start_date} 00:00"
    end_dt = f"{end_date} 23:59"
    metric = (metric or "plays").lower()
    ids = top_song_ids(start_dt, end_dt, int(top_n or 30), metric, int(cache_version or 0))

    if not ids:
        return False, "Keine Songs für den aktuellen Zeitraum/Metrik gefunden.", None

    # 2) Spotify Client
    auth = SpotifyServerAuth()
    sp = auth.get_authenticated_spotify_client()

    # 3) User ermitteln (falls Username nicht zentral konfiguriert ist)
    try:
        user_id = sp.current_user()["id"]
    except Exception:
        return False, "Spotify-User konnte nicht ermittelt werden (Auth prüfen).", None

    # 4) Playlist erstellen
    date_str = date.today().strftime("%Y-%m-%d")
    range_label = f"{start_date} bis {end_date}"
    default_name = f"SpotifyStats {date_str}"
    name = playlist_name or default_name
    desc = f"Top {len(ids)} Songs im Zeitraum {range_label}. Generiert mit SpotifyStats am {date_str}."

    try:
        # FIXME: wird ab märz brechen!
        pl = sp.user_playlist_create(user=user_id, name=name, public=public, description=desc)
        pl_id = pl["id"]
        pl_url = pl.get("external_urls", {}).get("spotify")

        # 5) Tracks hinzufügen (100 je Request)
        for batch in _chunk(ids, 100):
            sp.playlist_add_items(playlist_id=pl_id, items=batch)

        return True, f"Playlist '{name}' erstellt ({len(ids)} Titel).", pl_url
    except Exception as e:
        return False, f"Fehler beim Erstellen der Playlist: {e}", None

