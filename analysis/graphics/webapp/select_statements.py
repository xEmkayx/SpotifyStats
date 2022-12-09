import sys
# sys.path.append(r'C:\Users\Markus\PycharmProjects\Spotify_Stats')
import pandas as pd
from tools.DBOperations import dboperations


dbops = dboperations.DBOperations()


def allrounder() -> pd.DataFrame():
    sql_basic = """
        select distinct played_at, song_name, sh.song_id, artist_name, 
        artists.artist_id, album_name, albums.album_id, song_length
        from stream_history as sh
        JOIN songs on songs.song_id = sh.song_id
        JOIN art_songs as ars on ars.song_id = songs.song_id
        JOIN artists on artists.artist_id = ars.artist_id
        JOIN albums on albums.album_id = songs.album_id
        order by played_at asc;
        """

    print('Executing SQL statement...')

    sql_select_basic = dbops.custom_sql_statement(sql_basic)

    df_basic = pd.DataFrame(sql_select_basic, columns=['Gespielt am', 'Song', 'Song-ID', 'Künstler',
                                                       'Künstler-ID', 'Album', 'Album-ID', 'Songlänge'])

    print('5 most recent entries:')
    print(df_basic.tail(n=5).to_string())
    return df_basic
