import json
import time
import os

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from common.config.config import *


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class SpotifyAuthManager(metaclass=Singleton):
    def __init__(self):
        self.sp_oauth = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            open_browser=False,
            cache_path=TOKEN_CACHE_FILE_PATH
        )
        self._token_info = None  # Definiere _token_info hier im Konstruktor

    def get_auth_manager(self):
        return self.sp_oauth

    def get_auth_url(self):
        return self.sp_oauth.get_authorize_url()

    def generate_token_from_url(self, url):
        code = self.sp_oauth.parse_auth_response_url(url)[1]

        token_info = self.sp_oauth.get_access_token(code)

        if token_info:
            with open(TOKEN_CACHE_FILE_PATH, 'w') as file:
                json.dump(token_info, file)

        return token_info

    def load_token(self):
        try:
            if os.path.isfile(TOKEN_CACHE_FILE_PATH):
                with open(TOKEN_CACHE_FILE_PATH, 'r') as file:
                    self._token_info = json.load(file)
        except Exception as e:
            print(f"Failed to load token: {e}")

    def save_token(self):
        try:
            with open(TOKEN_CACHE_FILE_PATH, 'w') as file:
                json.dump(self._token_info, file)
        except Exception as e:
            print(f"Failed to save token: {e}")

    def refresh_if_needed(self):
        # Prüfe und erneuere das Token bei Bedarf
        if self._token_info and (self._token_info['expires_at'] - int(time.time()) < 60):
            new_token_info = self.sp_oauth.refresh_access_token(self._token_info['refresh_token'])
            new_token_info['expires_at'] = int(time.time()) + new_token_info['expires_in']
            self._token_info = new_token_info
            self.save_token()

    def get_access_token(self):
        return self._token_info.get('access_token') if self._token_info else None


def get_authenticated_spotify_client():
    spotify_manager = SpotifyAuthManager()
    spotify_manager.load_token()
    if not spotify_manager.get_access_token():
        print('No token')
        return None
    else:
        spotify_manager.refresh_if_needed()
        return spotipy.Spotify(auth=spotify_manager.get_access_token())
