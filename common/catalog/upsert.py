"""
    Schreibt Spotify-Track-Objekte in den Katalog (songs, albums, artists und
    die Zuordnungstabellen). Vorhandene Einträge werden aktualisiert statt
    übersprungen; jede inhaltliche Änderung landet in catalog_changes.

    Die Werte werden direkt aus dem (bereits dekodierten) JSON übernommen.
    Früher liefen sie durch json.dumps(), das Nicht-ASCII-Zeichen als \\uXXXX
    maskiert -> Kanji etc. landeten falsch in der DB.
"""
from sqlalchemy import text, bindparam

def _load(conn, sql: str, ids) -> dict:
    if not ids:
        return {}
    stmt = text(sql).bindparams(bindparam("ids", expanding=True))
    return {r[0]: r for r in conn.execute(stmt, {"ids": list(ids)})}


def log_changes(conn, changes: list[dict]):
    if changes:
        conn.execute(text("""
            INSERT INTO catalog_changes (entity, entity_id, field, old_value, new_value, source)
            VALUES (:entity, :entity_id, :field, :old_value, :new_value, :source)
        """), [{**c, "old_value": None if c["old_value"] is None else str(c["old_value"]),
                "new_value": None if c["new_value"] is None else str(c["new_value"])} for c in changes])


def apply_tracks(conn, tracks: list, source: str) -> dict:
    """
    Upsert für eine Liste von Track-Objekten, die jeweils sich selbst beschreiben
    (also nicht die relinkte Antwort für eine andere ID).
    :return: Zähler für neue/aktualisierte Einträge
    """
    tracks = [t for t in tracks if t and t.get("id")]
    if not tracks:
        return {"songs_new": 0, "songs_updated": 0, "changes": 0}

    albums, artists = {}, {}
    for t in tracks:
        al = t.get("album") or {}
        if al.get("id"):
            albums[al["id"]] = al
            for a in al.get("artists") or []:
                if a.get("id"):
                    artists[a["id"]] = a.get("name")
        for a in t.get("artists") or []:
            if a.get("id"):
                artists[a["id"]] = a.get("name")

    ex_artists = _load(conn, "SELECT artist_id, artist_name FROM artists WHERE artist_id IN :ids", artists)
    ex_albums = _load(conn, "SELECT album_id, album_name, album_type, release_date FROM albums WHERE album_id IN :ids",
                      albums)
    ex_songs = _load(conn, "SELECT song_id, song_name, album_id, isrc, duration_ms FROM songs WHERE song_id IN :ids",
                     [t["id"] for t in tracks])
    changes = []

    # Artists
    rows = []
    for aid, name in artists.items():
        old = ex_artists.get(aid)
        if old is not None and old[1] != name:
            changes.append({"entity": "artist", "entity_id": aid, "field": "name",
                            "old_value": old[1], "new_value": name, "source": source})
        if old is None or old[1] != name:
            rows.append({"id": aid, "name": name})
    if rows:
        conn.execute(text("""
            INSERT INTO artists (artist_id, artist_name) VALUES (:id, :name)
            ON DUPLICATE KEY UPDATE artist_name = VALUES(artist_name)
        """), rows)

    # Alben
    rows = []
    for alid, al in albums.items():
        old = ex_albums.get(alid)
        new = (al.get("name"), al.get("album_type"), (al.get("release_date") or "")[:10] or None)
        if old is not None and old[1] != new[0]:
            changes.append({"entity": "album", "entity_id": alid, "field": "name",
                            "old_value": old[1], "new_value": new[0], "source": source})
        if old is None or tuple(old[1:]) != new:
            rows.append({"id": alid, "name": new[0], "type": new[1], "release": new[2]})
    if rows:
        conn.execute(text("""
            INSERT INTO albums (album_id, album_name, album_type, release_date) VALUES (:id, :name, :type, :release)
            ON DUPLICATE KEY UPDATE album_name = VALUES(album_name), album_type = VALUES(album_type),
                                    release_date = VALUES(release_date)
        """), rows)
    album_artist_rows = [{"album": alid, "artist": a["id"]}
                         for alid, al in albums.items() for a in (al.get("artists") or []) if a.get("id")]
    if album_artist_rows:
        conn.execute(text("INSERT IGNORE INTO album_artists (album_id, artist_id) VALUES (:album, :artist)"),
                     album_artist_rows)

    # Songs
    rows, new_count, upd_count = [], 0, 0
    for t in tracks:
        sid = t["id"]
        isrc = (t.get("external_ids") or {}).get("isrc")
        new = {"name": t.get("name"), "album": (t.get("album") or {}).get("id"),
               "isrc": isrc, "duration": t.get("duration_ms")}
        old = ex_songs.get(sid)
        if old is None:
            new_count += 1
        else:
            for field, idx in (("name", 1), ("album_id", 2), ("isrc", 3)):
                old_val, new_val = old[idx], new["album" if field == "album_id" else field]
                # Fehlende ISRC nachtragen ist keine Änderung, nur ein Wechsel
                if old_val != new_val and not (field == "isrc" and old_val is None) and new_val is not None:
                    changes.append({"entity": "song", "entity_id": sid, "field": field,
                                    "old_value": old_val, "new_value": new_val, "source": source})
            if (old[1], old[2], old[3], old[4]) == (new["name"], new["album"], isrc, new["duration"]):
                continue
            upd_count += 1
        rows.append({"id": sid, **new, "duration": new["duration"] or 0})
    if rows:
        conn.execute(text("""
            INSERT INTO songs (song_id, song_name, album_id, isrc, duration_ms)
            VALUES (:id, :name, :album, :isrc, :duration)
            ON DUPLICATE KEY UPDATE song_name = VALUES(song_name), album_id = VALUES(album_id),
                isrc = COALESCE(VALUES(isrc), isrc),
                duration_ms = VALUES(duration_ms)
        """), rows)
    art_song_rows = [{"song": t["id"], "artist": a["id"]} for t in tracks for a in (t.get("artists") or []) if a.get("id")]
    if art_song_rows:
        conn.execute(text("INSERT IGNORE INTO art_songs (song_id, artist_id) VALUES (:song, :artist)"), art_song_rows)

    log_changes(conn, changes)
    return {"songs_new": new_count, "songs_updated": upd_count, "changes": len(changes)}
