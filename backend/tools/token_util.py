import time
from spotipy.oauth2 import SpotifyOAuth
import json
import os



scope = 'playlist-modify-public playlist-modify-private'


# todo: possibly delete class, since all logic is now in spotify_auth_manager.py
def token_exists(token_path):
    return os.path.isfile(token_path)


def load_token(token_path):
    if token_exists(token_path):
        with open(token_path, 'r') as file:
            token_info = json.load(file)
        return token_info
    else:
        return None


def refresh_if_needed(token_info):
    if token_info['expires_at'] - int(time.time()) < 60:  # Puffer von 60 Sekunden
        sp_oauth = SpotifyOAuth(
            client_id=os.getenv('CLIENT_ID'),
            client_secret=os.getenv('CLIENT_SECRET'),
            redirect_uri=os.getenv('REDIRECT_URI'),
            scope=scope,
            open_browser=False,
            # cache_path=constants.CACHE_FILE_NAME
        )
        # Aktualisiere den token
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])

        # Update expires_at and resave the info
        token_info['expires_at'] = int(time.time()) + token_info['expires_in']
        with open('spotify_token.json', 'w') as file:
            json.dump(token_info, file)

    return token_info


def get_auth_url():
    auth_manager = SpotifyOAuth(
        client_id=os.getenv('CLIENT_ID'),
        client_secret=os.getenv('CLIENT_SECRET'),
        redirect_uri=os.getenv('REDIRECT_URI'),
        scope=scope,
        open_browser=False,
        # cache_path=constants.CACHE_FILE_NAME,
        # show_dialog=True
    )
    return auth_manager.get_authorize_url()


def generate_token_from_url(url: str):
    sp_oauth = SpotifyOAuth(
        client_id=os.getenv('CLIENT_ID'),
        client_secret=os.getenv('CLIENT_SECRET'),
        redirect_uri=os.getenv('REDIRECT_URI'),
        scope=scope,
        open_browser=False,
        # cache_path=constants.CACHE_FILE_NAME,
        # show_dialog=True
    )

    code = sp_oauth.parse_auth_response_url(url)[1]

    token_info = sp_oauth.get_access_token(code)

    # if token_info:
    #     with open(constants.CACHE_FILE_NAME, 'w') as file:
    #         json.dump(token_info, file)

    return token_info
