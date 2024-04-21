"""
    Helper functions for the summary page
"""
import pandas as pd

from auth import spotify_auth_manager
from frontend.analysis.graphics.webapp.df_files import ndf_helper
from frontend.analysis.graphics.webapp.helpers import summary_cards, time_functions
from datetime import date, datetime
from dash import html
import dash_bootstrap_components as dbc

spotify = spotify_auth_manager.get_authenticated_spotify_client()


def get_top_songs_cards(df: pd.DataFrame, start_date: str = str(date(2010, 1, 1)), end_date: str = str(date.today()),
                        return_amount: int = 10, sorted_by_mins: bool = False):
    """

    :param df:
    :param start_date:
    :param end_date:
    :param return_amount: how many rows shall be returned; 0 for all rows
    :param sorted_by_mins:
    :return:
    """
    df_top_x = ndf_helper.get_top_songs_df(df=df,
                                           start_date=start_date,
                                           end_date=end_date,
                                           sorted_by_mins=sorted_by_mins)\
        .head(return_amount)
    """
    df_top_x = dataframe_helpers.get_top_songs_df(start_date=start_date, end_date=end_date,
                                                  sorted_by_mins=sorted_by_mins) \
        .head(return_amount)
    """

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


def get_top_artists_cards(df: pd.DataFrame, start_date: str = str(date(2010, 1, 1)), end_date: str = str(date.today()),
                          return_amount: int = 10):
    """
    df = dataframe_loader.get_default_dataframe()
    mask = date_mask(start_date, end_date)
    ndf = df.loc[mask]

    gr = ndf.groupby(['Artist', 'Artist-ID'], as_index=False).size()
    df_sorted = gr.sort_values(by=['size'], ascending=False)
    df_sorted.rename({1: 'Artist', 2: 'Artist-ID', 3: 'Stream Count'})
    df_sorted.set_axis(['Artist', 'Artist-ID', 'Stream Count'], axis=1, inplace=True)
    """
    # df_sorted = dataframe_helpers.get_top_artists(start_date=start_date, end_date=end_date)
    df_sorted = ndf_helper.get_top_artists(df=df, start_date=start_date, end_date=end_date)
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


def get_top_album_cards(df: pd.DataFrame, start_date: str = str(date(2010, 1, 1)), end_date: str = str(date.today()),
                        return_amount: int = 10):
    """
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
    """
    # df_combined = dataframe_helpers.get_top_albums(start_date=start_date, end_date=end_date)
    df_combined = ndf_helper.get_top_albums(df=df, start_date=start_date, end_date=end_date)
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


def init_songs(df: pd.DataFrame, start_date: str = str(date(datetime.now().year, 1, 1)),
               end_date: str = str(date(datetime.now().year, datetime.now().month, datetime.now().day)),
               amount: int = 10, sorted_by_minutes: bool = False, onscreen_songs: list = None):
    if onscreen_songs is None:
        onscreen_songs = []
    songs = []
    songs_wrapper = []
    onscreen_songs.clear()

    for idx, i in enumerate(
            get_top_songs_cards(df=df, start_date=start_date, end_date=end_date, return_amount=amount,
                                sorted_by_mins=sorted_by_minutes)):
        s_id = i.song_id
        onscreen_songs.append(s_id)

        wr = html.Li(
            children=[
                html.Img(src=i.song_image, alt='https://vectorified.com/images/no-profile-picture-icon-21.jpg'),
                html.Div(className='overlay', children=[
                    html.Span(f"{i.artist_name}"),
                    html.Br(),
                    html.Span(f'{i.song_name}'),
                    html.Br(),
                    html.Span(f'{i.album_name}'),
                    html.Br(),
                    html.Span(f"{i.streamed_amount}x gestreamed"),
                    html.Span(f'ca. {round(i.streamed_minutes, 2)} Minuten'),
                    html.Br(),
                    html.Span(f'({s_id})')
                ])
            ]
        )
        songs_wrapper.append(wr)
    ul_songs = html.Ul(className='ul-songs-summary', children=songs_wrapper)
    songs.append(ul_songs)

    sum_songs = html.Div(
        [dbc.Spinner(
            id='loading-summary-songs',
            color='primary',
            children=[
                html.Div(
                    id='div-summary-songs',
                    className='div-summary-songs',
                    children=songs
                )
            ]
        )]
    )
    return sum_songs, onscreen_songs


##############################

def init_artists(df: pd.DataFrame, start_date: str = str(date(datetime.now().year, 1, 1)),
                 end_date: str = str(date(datetime.now().year, datetime.now().month, datetime.now().day)),
                 amount: int = 10):
    artists = []
    artists_wrapper = []
    # for i in get_top_artists_cards(start_date=start_date, end_date=end_date, return_amount=amount):
    for i in get_top_artists_cards(df=df, start_date=start_date, end_date=end_date, return_amount=amount):
        wr = html.Li(
            children=[
                html.Img(src=i.artist_image, alt='https://vectorified.com/images/no-profile-picture-icon-21.jpg'),
                html.Div(className='overlay', children=[
                    html.Span(f'{i.artist_name}'),
                    html.Span(f'{i.streamed_amount}x gestreamed'),
                    html.Span(f'ca. {round(i.streamed_minutes, 2)} Minuten'),
                    html.Span(f'({i.artist_id})')
                ])
            ]
        )
        artists_wrapper.append(wr)

    ul_artists = html.Ul(className='ul-songs-summary', children=artists_wrapper)
    artists.append(ul_artists)

    sum_artists = html.Div([
        dbc.Spinner(
            id='loading-summary-artists',
            color='primary',
            children=[
                html.Div(
                    id='div-summary-artists',
                    className='div-summary-songs',
                    children=artists
                )])
    ])
    return sum_artists


#############################


def init_albums(df: pd.DataFrame, start_date: str = str(date(datetime.now().year, 1, 1)),
                end_date: str = str(date(datetime.now().year, datetime.now().month, datetime.now().day)),
                amount: int = 10):
    albums = []
    albums_wrapper = []
    # for i in get_top_album_cards(start_date=start_date, end_date=end_date, return_amount=amount):
    for i in get_top_album_cards(df=df, start_date=start_date, end_date=end_date, return_amount=amount):
        text = f'{i.album_artist} - {i.album_name}'
        wr = html.Li(
            children=[
                html.Img(src=i.album_image, alt=''),
                html.Div(className='overlay', children=[
                    html.Span(f'{i.album_artist}'),
                    html.Span(f'{i.album_name}'),
                    html.Span(f'({i.album_id})')
                ])
            ]
        )
        albums_wrapper.append(wr)
    ul_albums = html.Ul(className='ul-songs-summary', children=albums_wrapper)
    albums.append(ul_albums)

    sum_albums = html.Div([
        dbc.Spinner(
            id='loading-summary-albums',
            color='primary',
            children=[
                html.Div(
                    id='div-summary-albums',
                    className='div-summary-songs',
                    children=albums
                )],
            type='default'
        )])
    return sum_albums
