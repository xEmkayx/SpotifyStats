"""
    update all artist names in database that aren't encoded properly (not utf-8)
"""
import time

import requests

from auth import spotify_auth_manager
from common.db import dboperations
import traceback

desired_format = '%Y-%m-%d %H:%M:%S'


def main():
    dbops = dboperations.DBOperations()

    spotify = spotify_auth_manager.get_authenticated_spotify_client()

    # all_artists = dbops.select_from_table('artists', 'distinct artist_id, artist_name')
    all_artists = dbops.select_from_table('artists', 'distinct artist_id, artist_name',
                                          r'artist_name LIKE "%\\\%"')

    print(f'Started {__name__}')
    for artist in all_artists:
        tries = 0
        try:
            artist_id = artist[0]
            # artist_name = artist[1]
            artist_name = spotify.artist(artist_id)['name']
            dbops.update_artist_name(artist_id, artist_name)
            time.sleep(0.1)
            print(f'Updated: {artist_id} - {artist_name}')

        except requests.exceptions.ReadTimeout:
            if tries < 10:
                print(f'Timed out. Retrying.... Try {tries}/10')
                tries += 1
                time.sleep(10)
            else:
                print('Exiting...')
                exit()

        except:
            print(f'Error: {artist_id} - {artist_name}')
            traceback.print_exc()

    dbops.close_all()
    print(f'{__name__}: Done')


if __name__ == '__main__':
    main()
