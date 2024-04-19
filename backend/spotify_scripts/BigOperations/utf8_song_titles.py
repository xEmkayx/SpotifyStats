"""
    update all song names in database that aren't encoded properly (not utf-8)
"""
import time

import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from backend.tools.db import dboperations
from private.auth import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
from traceback import format_exc
from backend.tools.important_values import *

logging.basicConfig(
    level=log_level,
    format=log_format,
    datefmt=log_datefmt,
    filename=log_filename
)

dbops = dboperations.DBOperations()
desired_format = '%Y-%m-%d %H:%M:%S'

scope = 'user-library-read'

spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                                                    redirect_uri=REDIRECT_URI, scope=scope))
all_songs = dbops.select_from_table('songs', 'distinct song_id, song_name',
                                    r'song_name LIKE "%\\\%"')


def main():
    print(f'Started {__name__}')
    for song in all_songs:
        tries = 0
        try:
            song_id = song[0]
            song_name = spotify.track(song_id)['name']
            dbops.update_song_name(song_id, song_name)
            time.sleep(0.1)
            print(f'{song_id} --- {song_name}')

        except requests.exceptions.ReadTimeout:
            if tries < 10:
                print(f'Timed out. Retrying.... Try {tries}/10')
                tries += 1
                time.sleep(10)
            else:
                print('Exiting...')
                exit()
        except:
            logging.error(f'An error occured:\n{format_exc()}')

    dbops.close_all()
    print(f'{__name__}: Done')


if __name__ == '__main__':
    main()
