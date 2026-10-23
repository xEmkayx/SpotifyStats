"""
    Daten für die Summary-Seite. Nutzt dieselben (gecachten) Abfragen wie die
    Top-Seiten, damit identische Filter nur einmal gegen die DB laufen.
"""
from frontend_new.services.top_albums import cached_top_albums
from frontend_new.services.top_artists import cached_top_artists
from frontend_new.services.top_songs import cached_top_songs


def top_songs_data(start_dt, end_dt, limit, metric, cache_version):
    return cached_top_songs(start_dt, end_dt, int(limit), metric, cache_version)

def top_artists_data(start_dt, end_dt, limit, metric, cache_version):
    return cached_top_artists(start_dt, end_dt, int(limit), metric, cache_version)

def top_albums_data(start_dt, end_dt, limit, metric, cache_version):
    return cached_top_albums(start_dt, end_dt, int(limit), metric, cache_version)
