#!/usr/bin/env python
import logging
import os

from flask import Flask, request, jsonify

from backend import backend_main
from auth.spotify_auth_manager import SpotifyServerAuth
from backend.spotify_scripts import update_all

app = Flask(__name__)

# spotify = SpotifyAuthManager()
auth = SpotifyServerAuth()

# Poll interval in minutes; 0 disables the internal scheduler (e.g. to drive it
# externally). Default 30 -> safe against the 50-item cap of the Spotify API.
POLL_INTERVAL_MINUTES = int(os.getenv('POLL_INTERVAL_MINUTES', '25'))


def _scheduled_fetch():
    """Runs the recently-played fetch on a timer. Swallows errors (e.g. no token
    yet) so a single failure never tears down the scheduler."""
    try:
        backend_main.main()
        logging.info('Scheduled fetch completed.')
    except Exception:
        logging.exception('Scheduled fetch failed.')


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
    scheduler.start()
    logging.info(f'Internal scheduler started: every {POLL_INTERVAL_MINUTES} min.')

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
    update_all.main()
    return "Success", 200


# 0.0.0.0 instead of localhost for docker
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start_scheduler()
    app.run(host='0.0.0.0', port=9876)
    # app.run(host='localhost', port=9876)
