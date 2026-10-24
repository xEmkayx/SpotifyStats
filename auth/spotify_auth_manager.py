import threading

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from common.config.config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPE, AUTHORIZE_SCOPE, \
    TOKEN_CACHE_FILE_PATH


class SpotifyServerAuth:
    def __init__(self,
                 client_id = CLIENT_ID,
                 client_secret = CLIENT_SECRET,
                 redirect_uri = REDIRECT_URI,
                 scope = SCOPE,
                 token_cache_file_path = TOKEN_CACHE_FILE_PATH
                 ):
        self._lock = threading.Lock()
        self._params = dict(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri,
                            open_browser=False, cache_path=token_cache_file_path)
        self.oauth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,          # confidential client
        redirect_uri=redirect_uri,            # z.B. http://127.0.0.1:9876/callback
        scope=scope,
        open_browser=False,
        cache_path=token_cache_file_path
        )

    def _authorize_oauth(self):
        # Für die Anmeldung alle Berechtigungen anfragen (inkl. user-library-modify); geschrieben wird
        # in dieselbe Cache-Datei, die self.oauth liest
        return SpotifyOAuth(scope=AUTHORIZE_SCOPE, **self._params)

    def get_authorize_url(self, state=None):
        return self._authorize_oauth().get_authorize_url(state=state)

    def complete_authorization(self, code):
        # Tauscht code gegen Token; Spotipy speichert in cache_path
        self._authorize_oauth().get_access_token(code, check_cache=False)
        return True

    def granted_scopes(self) -> set:
        token = self.oauth.get_cached_token() or {}
        return set((token.get("scope") or "").split())

    def get_authenticated_spotify_client(self):
        # Liefert einen Spotify-Client, der Tokens automatisch refreshed
        return spotipy.Spotify(auth_manager=self.oauth)
