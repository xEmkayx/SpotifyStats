#!/usr/bin/env python
import os

from flask import Flask, request, jsonify

from backend import backend_main
from auth.spotify_auth_manager import SpotifyServerAuth
from backend.spotify_scripts import update_all

app = Flask(__name__)

# spotify = SpotifyAuthManager()
auth = SpotifyServerAuth()

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
    app.run(host='0.0.0.0', port=9876)
    # app.run(host='localhost', port=9876)
