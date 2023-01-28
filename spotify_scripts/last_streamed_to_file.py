import json
import logging
from traceback import format_exc

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from private.auth import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
from tools.important_values import *

logging.basicConfig(
    level=log_level,
    format=log_format,
    datefmt=log_datefmt,
    filename=log_filename
)


scope = 'user-read-recently-played user-library-read playlist-read-private ' \
        'playlist-read-collaborative user-top-read user-read-currently-playing'


def main():
    spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                                                        redirect_uri=REDIRECT_URI, scope=scope))

    last_streams = spotify.current_user_recently_played(limit=50)

    try:
        with open(last_streams_dir, 'w') as jf:
            jf.write(json.dumps(last_streams, indent=4))
        logging.info(f'Wrote to last_streams.json')
    except:
        logging.error(f'Error while writing file:\n{format_exc()}')


if __name__ == '__main__':
    main()
