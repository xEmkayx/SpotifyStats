#!/usr/bin/env python
from flask import Flask, request

from backend import backend_main
from auth.spotify_auth_manager import SpotifyAuthManager
from backend.spotify_scripts import update_all

app = Flask(__name__)

spotify = SpotifyAuthManager()


@app.route('/start')
def start():
    try:
        backend_main.main()
    except Exception as e:
        return "Error: " + str(e), 500
    return "Success", 200


@app.route('/getRedirectUrl')
def get_auth_url() -> str:
    return spotify.get_auth_url()


@app.route('/callback', methods=['POST'])
def callback():
    if request.is_json:
        url = request.get_json()
        print(url['url'])
        spotify.generate_token_from_url(url['url'])
        return "Abruf erfolgreich", 200

    return "Anforderung enthält kein JSON!", 400


@app.route('/db/update/all')
def db_update_all():
    update_all.main()
    return "Success", 200


# 0.0.0.0 instead of localhost for docker
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9876)
    # app.run(host='localhost', port=9876)
