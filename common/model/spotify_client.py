import os

import spotipy
from spotipy import SpotifyOAuth

from common.config.config import *
from backend.tools.token_util import *

#todo: possibly remove this class
class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class SpotifyClient(object, metaclass=Singleton):
    def __init__(self):
        self.sp_oauth = None

    def get_spotify_oauth(self) -> spotipy.oauth2.SpotifyOAuth:
        """
        Get Auth-manager of Spotify instance (spotipy.oauth2.SpotifyOAuth)
        :return:
        """
        if not self.sp_oauth:
            # Initialize the SpotifyOAuth only once
            self.sp_oauth = SpotifyOAuth(
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                redirect_uri=REDIRECT_URI,
                scope='user-read-private',
                open_browser=False,
                cache_path=TOKEN_CACHE_FILE_PATH
            )
        return self.sp_oauth
