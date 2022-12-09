"""
    Read all liked songs and write them to database
"""
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import mysql.connector
from tools.DBOperations import dboperations
from tools import calculations
from private.auth import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
import traceback

dbops = dboperations.DBOperations()
desired_format = '%Y-%m-%d %H:%M:%S'

scope = 'user-library-read'

spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                                                    redirect_uri=REDIRECT_URI, scope=scope))

liked_songs_path = './temp_files/liked_songs.json'


def main():
    offset = 0
    try:
        while True:
            last_streams = spotify.current_user_saved_tracks(offset=offset)

            with open(liked_songs_path, 'w') as jf:
                jf.write(json.dumps(last_streams, indent=4))

            f = open(liked_songs_path, 'r')
            jf = json.load(f)

            for item in jf['items']:
                song_id = json.dumps(item['track']['id'])
                song_id = song_id.replace('"', '')

                song_name = json.dumps(item['track']['name'])
                song_name = song_name.replace('"', '')

                artist_name = json.dumps(item['track']['artists'][0]['name'])
                artist_name = artist_name.replace('"', '')

                album_name = json.dumps(item['track']['album']['name'])
                album_name = album_name.replace('"', '')

                album_id = json.dumps(item['track']['album']['id'])
                album_id = album_id.replace('"', '')

                artist_id = json.dumps(item['track']['artists'][0]['id'])
                artist_id = artist_id.replace('"', '')

                song_length = json.dumps(item['track']['duration_ms'])
                song_length = song_length.replace('"', '')
                time.sleep(0.1)
                song_length = calculations.ms_to_timestring(int(song_length))
                time.sleep(0.1)

                # Write to artists
                for artist in item['track']['artists']:
                    artist_id = json.dumps(artist['id'])
                    artist_id = artist_id.replace('"', '')
                    val = (artist_id, artist_name)
                    try:
                        dbops.write_to_artists(val)
                    except mysql.connector.IntegrityError:
                        print(f'Duplicate entry at artists with Artist-id {artist_id}')
                        pass

                # write to albums
                val = (album_id, album_name)
                try:
                    dbops.write_to_albums(val)
                except mysql.connector.IntegrityError:
                    print(f'Duplicate entry at albums with album-id {album_id}')
                    pass

                # write to songs
                val = (song_id, song_name, album_id, song_length)
                try:
                    dbops.write_to_songs(val)
                except mysql.connector.IntegrityError:
                    print(f'Duplicate entry with Song-ID {song_id}')
                    pass

                # write to album_artists
                for artist in item['track']['album']['artists']:
                    artist_id = json.dumps(artist['id'])
                    artist_id = artist_id.replace('"', '')
                    val = (album_id, artist_id)
                    try:
                        dbops.get_album_artists(val)  # album_id, artist_id
                    except mysql.connector.IntegrityError:
                        print(f'Duplicate entry at album_artists with Artist-id {artist_id}')
                        pass
                    time.sleep(0.1)

                # write to artists_songs
                for artist in item['track']['artists']:
                    artist_id = json.dumps(artist['id'])
                    artist_id = artist_id.replace('"', '')
                    val = (song_id, artist_id)
                    try:
                        dbops.write_to_artists_songs(val)  # song_id, artist_id
                    except mysql.connector.IntegrityError:
                        print(f'Duplicate entry at artists_songs with Artist-id {artist_id}')
                        pass
                    time.sleep(0.1)
            offset += 10

    except:
        traceback.print_exc()

    finally:
        dbops.close_all()


if __name__ == '__main__':
    main()
