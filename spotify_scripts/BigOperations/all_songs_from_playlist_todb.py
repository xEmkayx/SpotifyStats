"""
    Add all songs from a playlist to the database
    (this is not an automated script. It's intended to be run manually.)
"""
import json
import os.path
import time
import traceback
from traceback import format_exc

import mysql.connector
import spotipy
from spotipy import SpotifyOAuth

from private.auth import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
from tools import calculations
from tools import last_streamed_methods as lsm
from tools.DBOperations import dboperations
from tools.important_values import *

logging.basicConfig(
    level=log_level,
    format=log_format,
    datefmt=log_datefmt,
    filename=log_filename
)

playlist_link = r'PLAYLIST_LINK'  # Insert playlist link here
playlist_id = r'55dmRytawB4Hqzu4XfEqoJ'  # Insert playlist ID here

scope = 'user-read-recently-played user-library-read playlist-read-private ' \
        'playlist-read-collaborative user-top-read user-read-currently-playing'


def main():
    offset = 0
    ct = offset
    try:
        dbops = dboperations.DBOperations()

        spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                                                            redirect_uri=REDIRECT_URI, scope=scope))

        playlist_items = spotify.playlist_items(playlist_id=playlist_id, offset=offset)

        try:
            with open(r'../../temp_files/playlist_todb.json', 'w') as jf:
                jf.write(json.dumps(playlist_items, indent=4))
            logging.info(f'Wrote to playlist_todb.json')
        except:
            logging.error(f'Error while writing file:\n{format_exc()}')

        with open('../../temp_files/playlist_todb.json', 'r') as f:
            jf = json.load(f)

            for item in jf['items']:
                song_id = json.dumps(item['track']['id'])
                song_id = lsm.clean_item(song_id)

                song_name = json.dumps(item['track']['name'])
                song_name = lsm.clean_item(song_name)

                artist_name = json.dumps(item['track']['artists'][0]['name'])
                artist_name = lsm.clean_item(artist_name)

                album_name = json.dumps(item['track']['album']['name'])
                album_name = lsm.clean_item(album_name)

                album_id = json.dumps(item['track']['album']['id'])
                album_id = lsm.clean_item(album_id)

                artist_id = json.dumps(item['track']['artists'][0]['id'])
                artist_id = lsm.clean_item(artist_id)

                song_length = json.dumps(item['track']['duration_ms'])
                song_length = lsm.clean_item(song_length)

                print(ct)
                ct += 1
                # print(f'ID: {song_id} -/- {artist_name} -- {song_name} /\\ {album_name}')

                time.sleep(0.1)
                song_length = calculations.ms_to_timestring(int(song_length))
                time.sleep(0.1)

                logging.info(
                    msg='\n' + 25 * '-/-' + '\n' + f'{artist_name} ----- {song_name}' + '\n' +
                        25 * '-/-' + '\n'
                )

                # all artists on song -> artists table
                artists = lsm.get_artists(item)
                for val in artists:
                    try:
                        dbops.write_to_artists(val)
                        logging.info(f'Wrote Artist {val[1]} with Artist-ID {val[0]} to {artists_tab_name} table.')
                    except mysql.connector.IntegrityError:
                        logging.error(f'Duplicate entry in {artists_tab_name} table with for Artist {val[1]} '
                                      f'with Artist-ID {val[0]}.')
                        pass
                    # Name zu lang
                    except:
                        print('artist')
                        logging.error(f'Error in the MYSQL Interface: \n'
                                      f'{format_exc()}')
                        artist_name = spotify.artist(song_id)['name']
                        print(artist_name)
                        pass

                # album -> albums table
                val = (album_id, album_name)
                try:
                    dbops.write_to_albums(val)
                    logging.info(f'Wrote Album {val+[1]} with Album-ID {val[0]} to {albums_tab_name} table.')
                except mysql.connector.IntegrityError:
                    logging.error(f'Duplicate entry in {albums_tab_name} table for Album {val[1]} with '
                                  f'Album-ID {album_id}')
                    pass
                except:
                    print('album')
                    logging.error(f'Error in the MYSQL Interface: \n'
                                  f'{format_exc()}')
                    album_name = spotify.album(album_id)['name']
                    print(album_name)
                    pass

                # song -> songs table
                val = (song_id, song_name, album_id, song_length)
                try:
                    dbops.write_to_songs(val)
                    logging.info(f'Wrote entry to {songs_tab_name} table for Song "{song_name}" with '
                                 f'Song-ID {song_id}')
                except mysql.connector.IntegrityError:
                    logging.error(f'Duplicate entry in {songs_tab_name} for Song "{song_name}" with Song-id {song_id}')
                    pass
                except:
                    print('song')
                    logging.error(f'Error in the MYSQL Interface: \n'
                                  f'{format_exc()}')
                    song_name = spotify.track(song_id)['name']
                    print(song_name)
                    pass

                # all artists on album -> album_artists table
                aartists = lsm.get_album_artists(item, album_id)
                for val in aartists:
                    try:
                        dbops.get_album_artists(val)
                        logging.info(f'Wrote entry to {album_artists_tab_name} table for Artist-ID {val[0]}')
                    except mysql.connector.IntegrityError:
                        logging.error(f'Duplicate entry in {album_artists_tab_name} table with Artist-id {val[0]}')
                        pass
                    except:
                        logging.error(f'Error in the MYSQL Interface: \n'
                                      f'{format_exc()}')
                        pass
                    time.sleep(0.1)

                # all artists on song -> artists_songs table
                sartists = lsm.get_artists_songs(item, song_id)
                for val in sartists:
                    try:
                        dbops.write_to_artists_songs(val)
                        logging.info(f'Wrote entry to {artists_songs_tab_name} table for Artist-ID {artist_id}')
                    except mysql.connector.IntegrityError:
                        logging.error(f'Duplicate entry at {artists_songs_tab_name} with Artist-id {artist_id}')
                        pass
                    except:
                        logging.error(f'Error in the MYSQL Interface: \n'
                                      f'{format_exc()}')
                        pass
                    time.sleep(0.1)

        try:
            os.remove(last_streams_dir)
            logging.info(f'Removed playlist_todb file.')
        except FileNotFoundError:
            logging.error(f'An error occured while trying to remove the file:\n'
                          f'{format_exc()}')
        finally:
            dbops.close_all()
            #dbops.mydb.close()

    except FileNotFoundError:
        logging.error(f'An error occured while trying to open the playlist_todb file:\n'
                      f'{format_exc()}')

    except:
        logging.error(f'An error occured while running the script:\n{format_exc()}')
        print('fehler', traceback.print_exception())
    finally:
        dbops.close_all()


if __name__ == '__main__':
    main()
