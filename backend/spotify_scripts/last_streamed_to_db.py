import json
from traceback import format_exc

from sqlalchemy import text, bindparam

from backend.tools import last_streamed_methods as lsm
from common.catalog.relations import rebuild_relations
from common.catalog.upsert import apply_tracks
from common.config.important_values import *
from common.db.engine import engine

logging.basicConfig(
    level=log_level,
    format=log_format,
    datefmt=log_datefmt,
    # filename=log_filename
)


def import_items(items: list) -> dict:
    """
    Schreibt "zuletzt gehört"-Einträge in die DB. Song/Artist/Album-Daten werden
    per Upsert aktualisiert (Namensänderungen landen in catalog_changes), die
    Werte kommen unverändert aus dem JSON (kein json.dumps -> Unicode bleibt korrekt).
    """
    items = [it for it in items if it.get("track") and it["track"].get("id")]
    if not items:
        return {"streams_new": 0, "songs_new": 0}

    with engine.begin() as conn:
        catalog = apply_tracks(conn, [it["track"] for it in items], source="import")
        streams = [{"played_at": str(lsm.format_played_at(it["played_at"])), "song_id": it["track"]["id"]}
                   for it in items]
        stmt = text("SELECT played_at FROM stream_history WHERE played_at IN :ids") \
            .bindparams(bindparam("ids", expanding=True))
        known = {r[0] for r in conn.execute(stmt, {"ids": [s["played_at"] for s in streams]})}
        new_streams = [s for s in streams if s["played_at"] not in known]
        if new_streams:
            conn.execute(text("INSERT INTO stream_history (played_at, song_id) VALUES (:played_at, :song_id)"),
                         new_streams)
    for s in new_streams:
        logging.info(f'Stream {s["played_at"]}: {s["song_id"]}')
    return {"streams_new": len(new_streams), "songs_new": catalog["songs_new"]}


def check_new_songs(song_ids: list):
    # Neue Songs sofort auf Relinking/ISRC prüfen, damit sie direkt richtig gruppiert werden
    from backend.catalog_sync import sync_songs
    try:
        sync_songs(song_ids, source="import")
        with engine.begin() as conn:
            rebuild_relations(conn)
    except Exception:
        logging.error(f'Katalog-Prüfung neuer Songs fehlgeschlagen:\n{format_exc()}')


def main():
    try:
        with open(last_streams_dir, 'r', encoding='utf-8') as f:
            items = json.load(f)['items']
    except FileNotFoundError:
        logging.error(f'An error occurred while trying to open the {last_streams_name} file:\n'
                      f'{format_exc()}')
        return

    with engine.connect() as conn:
        ids = list({it["track"]["id"] for it in items if it.get("track") and it["track"].get("id")})
        stmt = text("SELECT song_id FROM songs WHERE song_id IN :ids").bindparams(bindparam("ids", expanding=True))
        known_songs = {r[0] for r in conn.execute(stmt, {"ids": ids})} if ids else set()

    result = import_items(items)
    logging.info(f'Import: {result}')

    new_songs = [i for i in ids if i not in known_songs]
    if new_songs:
        check_new_songs(new_songs)

    try:
        os.remove(last_streams_dir)
        logging.info(f'Removed last_streams file.')
    except FileNotFoundError:
        logging.error(f'An error occurred while trying to remove the file:\n'
                      f'{format_exc()}')


if __name__ == '__main__':
    main()
