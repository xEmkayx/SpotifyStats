from datetime import date, datetime

import pandas
import pandas as pd

import spotipy
from spotipy import SpotifyOAuth

from analysis.graphics.webapp.helpers import summary_cards, time_functions
# from analysis.graphics.webapp.helpers.df_filenames import df_common_path, fn_df_allrounder
from private.auth import CLIENT_ID, REDIRECT_URI, CLIENT_SECRET
from analysis.graphics.webapp.df_files import dataframe_loader

spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                                                    redirect_uri=REDIRECT_URI, scope=''))

# df = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')
# df = dataframe_loader.get_default_dataframe()


def date_mask(start_date: str, end_date: str):
    df = dataframe_loader.get_default_dataframe()
    df['Played at'] = pd.to_datetime(df['Played at'], format='%Y-%m-%dT%H:%M')
    mask = (df['Played at'] >= start_date) & (df['Played at'] <= end_date)
    return mask


def get_top_songs(start_date: str = str(date(2010, 1, 1)), end_date: str = str(date.today()), return_amount: int = 10,
                  sorted_by_mins: bool = False):
    df = dataframe_loader.get_default_dataframe()
    mask = date_mask(start_date, end_date)
    ndf = df.loc[mask]

    if sorted_by_mins:
        df_combined = normalize_to_minutes(ndf.copy(deep=True))
    else:
        gr = ndf.groupby('Played at').agg(
            {'Song-ID': 'first', 'Song': 'first', 'Artist': ', '.join, 'Artist-ID': ', '.join,
             'Album': 'first', 'Album-ID': 'first', 'Song Length': 'first'})

        counted = gr.value_counts('Song-ID').rename({1: 'Song-ID', 2: 'Stream Count'}).sort_index().reset_index()
        counted.set_axis(['Song-ID', 'Stream Count'], axis=1, inplace=True)
        rest = gr.reset_index().drop('Played at', axis=1).drop_duplicates('Song-ID').sort_values('Song-ID')
        df_combined = pd.merge(counted, rest).sort_values('Stream Count', ascending=False)
    df_top_x = df_combined.head(return_amount)
    song_card_list: list[summary_cards.SongSummary] = []

    for index, row in df_top_x.iterrows():
        song_id = row['Song-ID']
        anz_streams = row['Stream Count']
        song_name = row['Song']
        artist_name = row['Artist']
        # artist_id = row['Artist-ID']
        album_name = row['Album']
        # album_id = row['Album-ID']
        song_length = f'00:{row["Song Length"]}'
        song_image = get_song_image(song_id)

        if len(df_top_x.columns) > 8:
            streamed_minutes = row['Streamed Mins']
        else:
            streamed_minutes = (time_functions.timestring_to_seconds(song_length) * anz_streams) / 60

        song_card_list.append(summary_cards.SongSummary(
            song_id=song_id,
            song_name=song_name,
            artist_name=artist_name,
            album_name=album_name,
            song_image=song_image,
            streamed_amount=anz_streams,
            streamed_minutes=streamed_minutes
            # streamed_minutes = song_length_seconds * anz_streams
        ))
    return song_card_list


def get_song_image(song_id: str):
    track = spotify.track(song_id)
    image_link = track['album']['images'][0]['url']
    return image_link


def get_top_artists(start_date: str = str(date(2010, 1, 1)), end_date: str = str(date.today()), return_amount: int = 10,
                  sorted_by_mins: bool = False):
    df = dataframe_loader.get_default_dataframe()
    mask = date_mask(start_date, end_date)
    ndf = df.loc[mask]

    gr = ndf.groupby(['Artist', 'Artist-ID'], as_index=False).size()
    df_sorted = gr.sort_values(by=['size'], ascending=False)
    df_sorted.rename({1: 'Artist', 2: 'Artist-ID', 3: 'Stream Count'})
    df_sorted.set_axis(['Artist', 'Artist-ID', 'Stream Count'], axis=1, inplace=True)

    df_top_x = df_sorted.head(return_amount)

    artist_card_list: list[summary_cards.ArtistSummary] = []

    for row in df_top_x.iterrows():
        artist_name = row[1][0]
        artist_id = row[1][1]
        anz_streams = row[1][2]
        artist_image = get_artist_image(artist_id)

        artist_card_list.append(summary_cards.ArtistSummary(
            artist_id=artist_id,
            artist_name=artist_name,
            artist_image=artist_image,
            streamed_amount=anz_streams
        ))
    return artist_card_list


def get_artist_image(artist_id: str):
    try:
        artist = spotify.artist(artist_id)
        img_link = artist['images'][0]['url']
        return img_link
    except IndexError:
        print(f'IndexError while fetching artist image with artist {artist_id}')
        return 'https://vectorified.com/images/no-profile-picture-icon-21.jpg'


def get_top_albums(start_date: str = str(date(2010, 1, 1)), end_date: str = str(date.today()), return_amount: int = 10,
                  sorted_by_mins: bool = False):
    df = dataframe_loader.get_default_dataframe()
    mask = date_mask(start_date, end_date)
    ndf = df.loc[mask]

    gr = ndf.groupby('Played at').agg({'Album': 'first', 'Album-ID': 'first',
                                        'Artist': ', '.join, 'Artist-ID': ', '.join,
                                        })
    counted = gr.value_counts('Album-ID').rename({1: 'Album-ID', 2: 'Stream Count'}).sort_index().reset_index()
    counted.set_axis(['Album-ID', 'Stream Count'], axis=1, inplace=True)
    rest = gr.reset_index().drop('Played at', axis=1).drop_duplicates('Album-ID').sort_values('Album-ID')
    df_combined = pd.merge(counted, rest).sort_values('Stream Count', ascending=False)

    df_top_x = df_combined.head(return_amount)

    album_card_list: list[summary_cards.AlbumSummary] = []

    for row in df_top_x.iterrows():
        album_id = row[1][0]
        anz_streams = row[1][1]
        album_name = row[1][2]
        album_artist = row[1][3]
        artist_id = row[1][4]
        album_image = get_album_image(album_id)

        album_card_list.append(summary_cards.AlbumSummary(
            album_id=album_id,
            album_name=album_name,
            album_artist=album_artist,
            album_image=album_image
        ))
    return album_card_list


def get_album_image(album_id: str):
    album = spotify.album(album_id)
    img_link = album['images'][0]['url']
    return img_link


def normalize_to_minutes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes a DataFrame, so it's sorted by its total streamed minutes
    :param df: DataFrame to normalize
    :return: normalized DataFrame
    """
    ndf = df
    gr = ndf.groupby('Played at').agg(
        {'Song-ID': 'first', 'Song': 'first', 'Artist': ', '.join, 'Artist-ID': ', '.join, 'Song Length': 'first',
         'Album': 'first', 'Album-ID': 'first'})

    counted = gr.value_counts('Song-ID').rename({1: 'Song-ID', 2: 'Stream Count'}).sort_index().reset_index()

    gr['Song Length'] = pd.to_datetime(gr['Song Length'], format='%H:%M:%S', errors='coerce').fillna(
        pd.to_datetime(gr['Song Length'],
                       format='%M:%S'))

    gr['Song Length'] = gr['Song Length'].dt.time
    gr['Song Length'] = gr['Song Length'].astype(str)

    counted.set_axis(['Song-ID', 'Stream Count'], axis=1, inplace=True)
    rest = gr.reset_index().drop('Played at', axis=1).drop_duplicates('Song-ID').sort_values('Song-ID')
    df_combined = pd.merge(counted, rest).sort_values('Stream Count', ascending=False)

    df_combined['Dauer Sekunden'] = pd.to_timedelta(df_combined['Song Length']).dt.total_seconds()
    df_combined['Streamed Mins'] = df_combined['Stream Count'] * (df_combined['Dauer Sekunden'] / 60)
    df_combined = df_combined.sort_values('Streamed Mins', ascending=False)
    return df_combined


if __name__ == '__main__':
    # get_top_songs()
    for i in get_top_artists():
        print(i.artist_image)

"""
Startdate - <class 'str'>: 2023-1-28
Enddate - <class 'str'>: 2023-01-29
"""
