import json
import os.path
import time
from traceback import format_exc

import mysql.connector
import spotipy
from spotipy import SpotifyOAuth

from auth import spotify_auth_manager
from backend.tools import calculations, last_streamed_methods as lsm
from common.db import dboperations
from common.config.important_values import *

logging.basicConfig(
    level=log_level,
    format=log_format,
    datefmt=log_datefmt,
    filename=log_filename
)


def main():
    try:
        dbops = dboperations.DBOperations()
        spotify = spotify_auth_manager.get_authenticated_spotify_client()

        with open(last_streams_dir, 'r') as f:
            jf = json.load(f)

            for item in jf['items']:
                played_at = json.dumps(item['played_at'])
                played_at = lsm.format_played_at(played_at)

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
                    logging.info(f'Wrote Album {val[1]} with Album-ID {val[0]} to {albums_tab_name} table.')
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

                # songs in history -> stream_history
                val = (played_at, song_id)
                try:
                    dbops.write_to_stream_history(val)
                    logging.info(f'Wrote entry to artists_songs table for timestamp {played_at}')
                except mysql.connector.IntegrityError:
                    logging.error(f'Duplicate entry at stream_history with timestamp {played_at}')
                    break

        try:
            os.remove(last_streams_dir)
            logging.info(f'Removed last_streams file.')
        except FileNotFoundError:
            logging.error(f'An error occurred while trying to remove the file:\n'
                          f'{format_exc()}')
        finally:
            dbops.close_all()
            # dbops.mydb.close()
        

    except FileNotFoundError:
        logging.error(f'An error occurred while trying to open the {last_streams_name} file:\n'
                      f'{format_exc()}')
    except:
        logging.error(f'An error occurred while running the script:\n{format_exc()}')


if __name__ == '__main__':
    main()
