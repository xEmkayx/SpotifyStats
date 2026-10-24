import json
from datetime import datetime


def clean_item(item: str) -> str:
    return item.replace('"', '')


def format_played_at(played_at: str) -> datetime:
    # Spotify liefert UTC ("...Z"); gespeichert wird UTC (stream_history.played_at DATETIME(3)).
    # Die Umrechnung in Ortszeit inkl. Sommerzeit passiert erst bei der Anzeige.
    played_at = clean_item(played_at)
    try:
        played_at = datetime.strptime(played_at, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        played_at = datetime.strptime(played_at, "%Y-%m-%dT%H:%M:%SZ")
    # DATETIME(3): auf Millisekunden kürzen, damit der Duplikat-Abgleich exakt greift
    return played_at.replace(microsecond=played_at.microsecond // 1000 * 1000)


def get_artists(item: json) -> list:
    artists = []
    for artist in item['track']['artists']:
        artist_id = json.dumps(artist['id'])
        artist_id = clean_item(artist_id)
        artist_name = json.dumps(artist['name'])
        artist_name = clean_item(artist_name)
        val = (artist_id, artist_name)
        artists.append(val)
    return artists


def get_artists_track(item: json) -> list:
    artists = []
    for artist in item['artists']:
        artist_id = json.dumps(artist['id'])
        artist_id = clean_item(artist_id)
        artist_name = json.dumps(artist['name'])
        artist_name = clean_item(artist_name)
        val = (artist_id, artist_name)
        artists.append(val)
    return artists


def get_album_artists(item: json, album_id: str) -> list:
    artists = []
    for artist in item['track']['album']['artists']:
        artist_id = json.dumps(artist['id'])
        artist_id = clean_item(artist_id)
        val = (album_id, artist_id)
        artists.append(val)
    return artists


def get_artists_songs(item: json, song_id: str) -> list:
    artists = []
    for artist in item['track']['artists']:
        artist_id = json.dumps(artist['id'])
        artist_id = artist_id.replace('"', '')
        val = (song_id, artist_id)
        artists.append(val)
    return artists
