"""
    update all song names in database that aren't encoded properly (not utf-8)
"""
import time

import requests

from auth import spotify_auth_manager
from common.db import dboperations
from traceback import format_exc
from common.config.important_values import *

logging.basicConfig(
    level=log_level,
    format=log_format,
    datefmt=log_datefmt,
    filename=log_filename
)

desired_format = '%Y-%m-%d %H:%M:%S'


def main():
    dbops = dboperations.DBOperations()

    spotify = spotify_auth_manager.get_authenticated_spotify_client()

    all_songs = dbops.select_from_table('songs', 'distinct song_id, song_name',
                                        r'song_name LIKE "%\\\%"')

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
