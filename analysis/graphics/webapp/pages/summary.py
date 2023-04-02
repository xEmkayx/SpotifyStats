import dash
import dash_bootstrap_components as dbc
import plotly.express as px
from dash import html, dcc, callback, Input, Output, DiskcacheManager
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

from analysis.graphics.webapp.helpers import summary_helpers
from analysis.graphics.webapp.helpers.df_filenames import *
# import datetime
from analysis.graphics.webapp.helpers.time_functions import *
from analysis.graphics.webapp.select_statements import *
from spotify_scripts import playlist_creator

dash.register_page(__name__)

# df_orig = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')
# df = summary_helpers.normalize_to_minutes(df_orig).sort_values('Anzahl Streams')

onscreen_songs = []

# TODO: MORGENS/ABENDS
tommorow = date(datetime.now().year, datetime.now().month, datetime.now().day + 1)

datepicker = dcc.DatePickerRange(
    id='date-picker-summary',
    min_date_allowed=date(2010, 1, 1),
    max_date_allowed=tommorow,  # date(2022, 12, 12),  #
    initial_visible_month=date.today(),  # date(2022, 11, 1),  #
    end_date=tommorow,
    start_date=date(datetime.now().year, 1, 1)
)


def init_songs(start_date: str = str(date(datetime.now().year, 1, 1)),
               end_date: str = str(date(datetime.now().year, datetime.now().month, datetime.now().day)),
               amount: int = 10, sorted_by_minutes: bool = False):
    songs = []
    songs_wrapper = []
    global onscreen_songs
    onscreen_songs.clear()

    """
    while len(onscreen_songs) > 0:
        # onscreen_songs.clear()
        onscreen_songs = []
    """
    # print(f'initsongs: initial length of onscreensongs: {len(onscreen_songs)}')

    for idx, i in enumerate(
            summary_helpers.get_top_songs(start_date=start_date, end_date=end_date, return_amount=amount,
                                          sorted_by_mins=sorted_by_minutes)):
        """
        text = f"{i.artist_name} - {i.song_name}\n{i.album_name}\n " \
               f"Gestreamt: {i.streamed_amount} Mal -> ca. {i.streamed_minutes} Minuten"
        """
        id = i.song_id
        onscreen_songs.append(id)
        # print(f'idx: {idx}, song_id: {id}, length onscreensongs: {len(onscreen_songs)}')

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
                    html.Span(f'({id})')
                ])
            ]
        )
        songs_wrapper.append(wr)
    ul_songs = html.Ul(className='ul-songs-summary', children=songs_wrapper)
    songs.append(ul_songs)

    sum_songs = html.Div(
        id='div-summary-songs',
        className='div-summary-songs',
        children=songs
    )
    return sum_songs


# summary_songs = init_songs()
summary_songs = sum_songs = html.Div(
    id='div-summary-songs',
    className='div-summary-songs'
)

tab_songs = dbc.Tab(
    [
        dcc.Loading(
            [summary_songs],
            id='load-summary-songs'
        )
    ],
    label='Songs'
)


##############################

def init_artists(start_date: str = str(date(datetime.now().year, 1, 1)),
                 end_date: str = str(date(datetime.now().year, datetime.now().month, datetime.now().day)),
                 amount: int = 10):
    artists = []
    artists_wrapper = []
    for i in summary_helpers.get_top_artists(start_date=start_date, end_date=end_date, return_amount=amount):
        """
        text = f'{i.artist_name}<br> {i.artist_id}<br> ' \
               f'Gestreamt: {i.streamed_amount} -> ca. {i.streamed_minutes} Minuten'
        """
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

    sum_artists = html.Div(
        id='div-summary-artists',
        className='div-summary-songs',
        children=artists
    )
    return sum_artists


# summary_artists = init_artists()
summary_artists = html.Div(
    id='div-summary-artists',
    className='div-summary-songs'
)
tab_artists = dbc.Tab(
    [
        dcc.Loading(
            [summary_artists],
            id='load-summary-artists'
        )
    ],
    label='Artists'
)


#############################


def init_albums(start_date: str = str(date(datetime.now().year, 1, 1)),
                end_date: str = str(date(datetime.now().year, datetime.now().month, datetime.now().day)),
                amount: int = 10):
    albums = []
    albums_wrapper = []
    for i in summary_helpers.get_top_albums(start_date=start_date, end_date=end_date, return_amount=amount):
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

    sum_albums = html.Div(
        id='div-summary-albums',
        className='div-summary-songs',
        children=albums
    )
    return sum_albums


# summary_albums = init_albums()
summary_albums = html.Div(
    id='div-summary-albums',
    className='div-summary-songs'
)
tab_albums = dbc.Tab(
    [
        dcc.Loading(
            [summary_albums],
            id='load-summary-albums'
        )
    ],
    label='Albums'
)

button_7d = dbc.Button(
    'Letzte 7 Tage',
    id='button-7d-summary',
    outline=True,
    color='primary',
    n_clicks=0
)

button_month = dbc.Button(
    'Letzter Monat',
    id='button-month-summary',
    outline=True,
    color='primary',
    n_clicks=0
)

button_year = dbc.Button(
    'Letztes Jahr',
    id='button-year-summary',
    outline=True,
    color='primary',
    n_clicks=0
)

date_buttons = dbc.ButtonGroup(
    id='btn-group-summary',
    children=[
        button_7d,
        button_month,
        button_year
    ]
)

tabs = dcc.Tabs(
    [
        tab_songs,
        tab_artists,
        tab_albums
    ],
    parent_className='custom-tabs',
    className='custom-tabs-container'
)

# amount_tb = dbc.Input(
amount_tb = dbc.Input(
    id='inp-amount',
    type='number',
    value=10,
    className='inp-summary'
)

playlist_button = dbc.Button(
    'Create a Playlist from these Songs',
    id='button-playlist',
    outline=True,
    color='primary',
    n_clicks=0
)

streamed_by_buttons = html.Div(
    [
        dbc.RadioItems(
            id="streamed-by-radios",
            className="btn-group",
            inputClassName="btn-check",
            labelClassName="btn btn-outline-primary",
            labelCheckedClassName="active",
            options=[
                {"label": "Sort by total count of Streams", "value": 1},
                {"label": "Sort by total streamed minutes", "value": 2},
            ],
            value=1,
        )
    ],
    className="radio-group",
)

layout = html.Div(children=[
    html.H1(children='Summary'),
    datepicker,
    html.Br(),
    date_buttons,
    amount_tb,
    playlist_button,
    streamed_by_buttons,
    tabs
])


@callback(
    Output('button-playlist', 'n_clicks'),
    [Input("button-playlist", 'n_clicks'),
     Input('date-picker-summary', 'start_date'),
     Input('date-picker-summary', 'end_date'),
     ],
)
def create_playlist_buttonclick(n_clicks, start_date, end_date):
    if n_clicks is not None and n_clicks > 0:
        # print(f'Length of onscreen songs: {len(onscreen_songs)}\nonscreen_songs:')
        # print(onscreen_songs.sort())
        playlist_creator.create_playlist(song_ids=onscreen_songs, range=f'{start_date} - {end_date}')


@callback(
    Output('date-picker-summary', 'start_date'),
    Output('date-picker-summary', 'end_date'),
    Output('button-7d-summary', 'n_clicks'),
    Output('button-month-summary', 'n_clicks'),
    Output('button-year-summary', 'n_clicks'),

    [Input("button-7d-summary", "n_clicks"),
     Input('button-month-summary', 'n_clicks'),
     Input('button-year-summary', 'n_clicks')
     ],
)
def button_events_graph(b7d, bmonth, byear):
    if b7d != 0:
        res = get_7days()
    elif bmonth != 0:
        res = get_last_month()
    elif byear != 0:
        res = get_last_year()
    else:
        res = get_standard_time()

    s_date = res[0]
    e_date = res[1]

    return s_date, e_date, 0, 0, 0


# TODO: albums werden nicht richtig gefetcht
# TODO: Linebreaks funktionieren nicht richtig
@callback(
    Output('div-summary-songs', 'children'),
    Output('div-summary-artists', 'children'),
    Output('div-summary-albums', 'children'),

    [Input('date-picker-summary', 'start_date'),
     Input('date-picker-summary', 'end_date'),
     Input('inp-amount', 'value'),
     Input("streamed-by-radios", "value")],
)
def update_tabs(start_date, end_date, amount, radio_values):
    sorted_by_minutes = False
    if radio_values == 1:
        sorted_by_minutes = False
    else:
        sorted_by_minutes = True

    songs = init_songs(start_date, end_date, amount, sorted_by_minutes)
    artists = init_artists(start_date, end_date, amount)
    albums = init_albums(start_date, end_date, amount)

    return songs, artists, albums
