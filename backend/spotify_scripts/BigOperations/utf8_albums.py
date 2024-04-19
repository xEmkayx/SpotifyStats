"""
    update all album names in database that aren't encoded properly (not utf-8)
"""
import time

import requests

from auth import spotify_auth_manager
from common.db import dboperations
import traceback

dbops = dboperations.DBOperations()
desired_format = '%Y-%m-%d %H:%M:%S'


spotify = spotify_auth_manager.get_authenticated_spotify_client()

all_albums = dbops.select_from_table('albums', 'distinct album_id, album_name',
                                     r'album_name LIKE "%\\\%"')
# all_albums = dbops.select_from_table('albums', 'distinct album_id, album_name')
print(all_albums)


def main():
    print(f'Started {__name__}')
    for album in all_albums:
        tries = 0
        try:
            album_id = album[0]
            print(album_id)
            album_name = spotify.album(album_id)['name']
            dbops.update_album_name(album_id, album_name)
            time.sleep(0.1)
            print(f'{album_id} --- {album_name}')

        except requests.exceptions.ReadTimeout:
            if tries < 10:
                print(f'Timed out. Retrying.... Try {tries}/10')
                tries += 1
                time.sleep(10)
            else:
                print('Exiting...')
                exit()

        except:
            print(f'Error: {album_id} - {album_name}')
            traceback.print_exc()

    dbops.close_all()
    print(f'{__name__}: Done')


if __name__ == '__main__':
    main()
    # id = '39C4T9TCMg6yjleEADxDq4'
    # print(spotify.album(id))
