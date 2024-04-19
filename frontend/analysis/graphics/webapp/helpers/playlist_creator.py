from datetime import datetime
from traceback import format_exc

from auth import spotify_auth_manager
from common.config.config import SPOTIFY_USERNAME

# todo: reimplement
# from backend.tools.important_values import *

# logging.basicConfig(
#     level=log_level,
#     format=log_format,
#     datefmt=log_datefmt,
#     filename=log_filename
# )

scope = 'playlist-modify-public playlist-modify-private'


def create_playlist(song_ids: list, range: str):
    try:
        """
        if len(song_ids) > 50:
            rest = len(song_ids) % 50
            for i in rest:
                pass
        """
        if len(song_ids) > 0:
            # print(f'song_ids: {song_ids}')
            # res = [*set(song_ids)]
            res = []
            [res.append(x) for x in song_ids if x not in res]
            # print(f'res: {res}')
            current_date = datetime.today().strftime('%Y-%m-%d')

            playlist_name = f'SpotifyStats {current_date}'
            playlist_description = f'Top {len(res)} songs in the range of {range}.' \
                                   f'\nThis playlist was generated with SpotifyStats on {current_date}'
            spotify = spotify_auth_manager.get_authenticated_spotify_client()

            playlist = spotify.user_playlist_create(user=SPOTIFY_USERNAME, name=playlist_name, description=playlist_description)
            spotify.playlist_add_items(playlist_id=playlist['id'], items=res)
        else:
            # logging.error('Playlist Creator: length of "song_ids" invalid')
            print('Playlist Creator: length of "song_ids" invalid')

    except:
        # logging.error(f'Error while creating a playlist: {format_exc()}')
        print(f'Error while creating a playlist: {format_exc()}')
