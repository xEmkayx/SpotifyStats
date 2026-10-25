import threading

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from common.config.config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPE, AUTHORIZE_SCOPE, \
    TOKEN_CACHE_FILE_PATH


class ScopePreservingOAuth(SpotifyOAuth):
    """
    spotipy überschreibt beim stündlichen Erneuern des Tokens die gespeicherte Berechtigungsliste mit den
    Berechtigungen, die dieses Objekt anfragt (self.scope). Dadurch "verschwinden" zusätzlich erteilte
    Berechtigungen wie user-library-modify aus dem Cache, obwohl Spotify sie weiter gewährt.
    Hier wird stattdessen gespeichert, was Spotify tatsächlich zurückmeldet.
    """

    def _add_custom_values_to_token_info(self, token_info):
        granted = token_info.get("scope")
        token_info = super()._add_custom_values_to_token_info(token_info)
        if granted:
            token_info["scope"] = granted
        return token_info


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
        self.oauth = ScopePreservingOAuth(
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
        return ScopePreservingOAuth(scope=AUTHORIZE_SCOPE, **self._params)

    def get_authorize_url(self, state=None):
        return self._authorize_oauth().get_authorize_url(state=state)

    def complete_authorization(self, code):
        # Tauscht code gegen Token; Spotipy speichert in cache_path
        self._authorize_oauth().get_access_token(code, check_cache=False)
        return True

    def granted_scopes(self) -> set:
        token = self.oauth.get_cached_token() or {}
        return set((token.get("scope") or "").split())

    def get_authenticated_spotify_client(self, wait_on_rate_limit: bool = True):
        """
        Spotify-Client, der Tokens automatisch erneuert.
        wait_on_rate_limit=False: bei 429 nicht still warten (spotipy schläft sonst die komplette
        Retry-After-Zeit, teils viele Minuten), sondern SpotifyException(429) mit Retry-After-Header werfen.
        """
        if wait_on_rate_limit:
            return spotipy.Spotify(auth_manager=self.oauth, requests_timeout=20)
        return spotipy.Spotify(auth_manager=self.oauth, requests_timeout=20, status_forcelist=(500, 502, 503, 504))
