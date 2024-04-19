from flask import Flask, request

import backend.backend_main
from backend.spotify_scripts import update_all
from backend.tools import token_util

app = Flask(__name__)


@app.route('/start')
def callback():
    backend.backend_main.main()
    return "Success", 200


@app.route('/getRedirectUrl')
def get_auth_url() -> str:
    return token_util.get_auth_url()


@app.route('/callback', methods=['POST'])
def callback():
    if request.is_json:
        url = request.get_json()
        print(url['url'])
        token_util.generate_token_from_url(url['url'])
        return "Abruf erfolgreich", 200

    return "Anforderung enthält kein JSON!", 400


@app.route('/db/update/all')
def db_update_all():
    update_all.main()
    return "Success", 200


if __name__ == '__main__':
    app.run(host='localhost', port=9876)
