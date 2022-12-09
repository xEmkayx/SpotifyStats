"""
    update all album names in database that aren't encoded properly (not utf-8)
"""
import time

import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from tools.DBOperations import dboperations
from private.auth import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
import traceback

dbops = dboperations.DBOperations()
desired_format = '%Y-%m-%d %H:%M:%S'

# print(json.dumps(jf, indent=4))
scope = 'user-library-read'

spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                                                    redirect_uri=REDIRECT_URI, scope=scope))

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
