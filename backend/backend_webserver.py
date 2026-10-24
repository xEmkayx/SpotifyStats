#!/usr/bin/env python
import logging
import os

from flask import Flask, request, jsonify

from backend import backend_main, catalog_sync
from auth.spotify_auth_manager import SpotifyServerAuth
from common.db import migrate

app = Flask(__name__)

# spotify = SpotifyAuthManager()
auth = SpotifyServerAuth()

# Poll interval in minutes; 0 disables the internal scheduler (e.g. to drive it
# externally). Default 30 -> safe against the 50-item cap of the Spotify API.
POLL_INTERVAL_MINUTES = int(os.getenv('POLL_INTERVAL_MINUTES', '25'))
# Nächtlicher rollierender Katalog-Abgleich (Stunde in lokaler Zeit, -1 = aus)
CATALOG_SYNC_HOUR = int(os.getenv('CATALOG_SYNC_HOUR', '4'))
# Abgleich eigener Playlists + Lieblingssongs (0 = aus)
PLAYLIST_SYNC_MINUTES = int(os.getenv('PLAYLIST_SYNC_MINUTES', '60'))


def _scheduled_fetch():
    """Runs the recently-played fetch on a timer. Swallows errors (e.g. no token
    yet) so a single failure never tears down the scheduler."""
    try:
        backend_main.main()
        logging.info('Scheduled fetch completed.')
    except Exception:
        logging.exception('Scheduled fetch failed.')


def _scheduled_catalog_sync():
    try:
        catalog_sync.rolling_sync()
    except Exception:
        logging.exception('Scheduled catalog sync failed.')


def _scheduled_playlist_sync():
    try:
        from common.playlists import bulk, history
        sp = auth.get_authenticated_spotify_client()
        history.sync_all(sp)
        # Veraltete Versionen austauschen, falls in den Einstellungen aktiviert
        bulk.run_auto_replace(sp)
    except Exception:
        logging.exception('Scheduled playlist sync failed.')


def start_scheduler():
    if POLL_INTERVAL_MINUTES <= 0:
        logging.info('POLL_INTERVAL_MINUTES <= 0, internal scheduler disabled.')
        return
    from datetime import datetime
    from apscheduler.schedulers.background import BackgroundScheduler

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        _scheduled_fetch,
        trigger='interval',
        minutes=POLL_INTERVAL_MINUTES,
        max_instances=1,   # skip a tick if the previous run is still going
        coalesce=True,     # collapse missed runs into one
        next_run_time=datetime.now(),  # kick once right after startup
        id='recently_played_fetch',
    )
    if CATALOG_SYNC_HOUR >= 0:
        scheduler.add_job(
            _scheduled_catalog_sync,
            trigger='cron',
            hour=CATALOG_SYNC_HOUR,
            max_instances=1,
            coalesce=True,
            id='catalog_rolling_sync',
        )
    if PLAYLIST_SYNC_MINUTES > 0:
        scheduler.add_job(
            _scheduled_playlist_sync,
            trigger='interval',
            minutes=PLAYLIST_SYNC_MINUTES,
            max_instances=1,
            coalesce=True,
            next_run_time=datetime.now(),
            id='playlist_sync',
        )
    scheduler.start()
    logging.info(f'Internal scheduler started: every {POLL_INTERVAL_MINUTES} min, '
                 f'catalog sync daily at {CATALOG_SYNC_HOUR}:00, playlists every {PLAYLIST_SYNC_MINUTES} min.')

@app.route('/start')
def start():
    try:
        backend_main.main()
    except Exception as e:
        return "Error: " + str(e), 500
    return "Success", 200


@app.route("/auth/start")
def auth_start():
    state = os.urandom(16).hex()
    url = auth.get_authorize_url(state=state)
    return jsonify({"authorize_url": url, "state": state})

@app.route("/auth/complete", methods=["POST"])
def auth_complete():
    data = request.get_json(force=True)
    code = data.get("code")
    state = data.get("state")  # prüfe gegen zuvor ausgegebenen state
    if not code:
        return "missing code", 400
    auth.complete_authorization(code)
    return "ok", 200


@app.route('/db/update/all')
def db_update_all():
    # Vollständiger Katalog-Abgleich (Namen, Unicode-Reparatur, ISRC, Relinking) im Hintergrund
    if not catalog_sync.full_sync_in_background():
        return "Catalog sync already running", 409
    return "Catalog sync started", 202


# 0.0.0.0 instead of localhost for docker
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    migrate.upgrade()  # Alembic: Schema auf den neuesten Stand bringen
    start_scheduler()
    app.run(host='0.0.0.0', port=9876)
    # app.run(host='localhost', port=9876)
