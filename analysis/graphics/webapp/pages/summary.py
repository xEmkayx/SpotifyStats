import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output, DiskcacheManager
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

from analysis.graphics.webapp.helpers import summary_helpers
from analysis.graphics.webapp.helpers.time_functions import *
from spotify_scripts import playlist_creator

dash.register_page(__name__)

onscreen_songs = []

# TODO: MORGENS/ABENDS
tomorrow = date(datetime.now().year, datetime.now().month, datetime.now().day + 1)

datepicker = dcc.DatePickerRange(
    id='date-picker-summary',
    min_date_allowed=date(2010, 1, 1),
    max_date_allowed=tomorrow,  # date(2022, 12, 12),  #
    initial_visible_month=date.today(),  # date(2022, 11, 1),  #
    end_date=tomorrow,
    start_date=date(datetime.now().year, 1, 1)
)


def init_songs(start_date: str = str(date(datetime.now().year, 1, 1)),
               end_date: str = str(date(datetime.now().year, datetime.now().month, datetime.now().day)),
               amount: int = 10, sorted_by_minutes: bool = False):
    songs = []
    songs_wrapper = []
    global onscreen_songs
    onscreen_songs.clear()

    for idx, i in enumerate(
            summary_helpers.get_top_songs_cards(start_date=start_date, end_date=end_date, return_amount=amount,
                                                sorted_by_mins=sorted_by_minutes)):
        id = i.song_id
        onscreen_songs.append(id)

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
        [dcc.Loading(
            id='loading-summary-songs',
            children=[html.Div(
                id='div-summary-songs',
                className='div-summary-songs',
                children=songs
            )]
        )]
    )
    return sum_songs


##############################

def init_artists(start_date: str = str(date(datetime.now().year, 1, 1)),
                 end_date: str = str(date(datetime.now().year, datetime.now().month, datetime.now().day)),
                 amount: int = 10):
    artists = []
    artists_wrapper = []
    for i in summary_helpers.get_top_artists_cards(start_date=start_date, end_date=end_date, return_amount=amount):
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
        dcc.Loading(
            id='loading-summary-artists',
            children=[
                html.Div(
                    id='div-summary-artists',
                    className='div-summary-songs',
                    children=artists
                )])
    ])
    return sum_artists


#############################


def init_albums(start_date: str = str(date(datetime.now().year, 1, 1)),
                end_date: str = str(date(datetime.now().year, datetime.now().month, datetime.now().day)),
                amount: int = 10):
    albums = []
    albums_wrapper = []
    for i in summary_helpers.get_top_album_cards(start_date=start_date, end_date=end_date, return_amount=amount):
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
        dcc.Loading(
            id='loading-summary-albums',
            children=[
                html.Div(
                    id='div-summary-albums',
                    className='div-summary-songs',
                    children=albums
                )],
            type='default'
        )])
    return sum_albums


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
    className='date-buttons',
    children=[
        button_7d,
        button_month,
        button_year
    ]
)

tabs = dcc.Tabs(
    children=[
        dcc.Tab(label='Songs', value='tab-songs-summary'),
        dcc.Tab(label='Artists', value='tab-artists-summary'),
        dcc.Tab(label='Albums', value='tab-albums-summary'),
    ],
    parent_className='custom-tabs',
    className='custom-tabs-container',
    id='summary-tabs',
    value='tab-songs-summary'
)

amount_tb = dbc.Input(
    id='inp-amount',
    type='number',
    value=10,
    className='inp-summary',
    style={
        'width': '4%',
        'margin-left': '5px',
        'margin-right': '5px',
        'display': 'inline-block',
        # 'filter': 'contrast(200%)',
    }
)

playlist_button = dbc.Button(
    'Create a Playlist from these Songs',
    id='button-playlist',
    # outline=True,
    color='success',
    n_clicks=0,
    className='create-playlist-button'
)

streamed_by_buttons = html.Div(
    [
        dbc.RadioItems(
            id="summary-streamed-by-radios",
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

content = html.Div(
    id='summary-content-div'
)

layout = html.Div(children=[
    html.H1(children='Summary'),
    datepicker,
    amount_tb,
    html.Br(),
    date_buttons,
    html.Br(),
    streamed_by_buttons,
    playlist_button,
    tabs,
    content
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
    Output('summary-content-div', 'children'),

    [Input('date-picker-summary', 'start_date'),
     Input('date-picker-summary', 'end_date'),
     Input('inp-amount', 'value'),
     Input("summary-streamed-by-radios", "value"),
     Input('summary-tabs', 'value')],
)
def update_tabs(start_date, end_date, amount, radio_values, selected_tab):
    sorted_by_minutes = False
    if radio_values == 1:
        sorted_by_minutes = False
    else:
        sorted_by_minutes = True

    match selected_tab:
        case 'tab-artists-summary':
            t = init_artists(start_date, end_date, amount)
        case 'tab-albums-summary':
            t = init_albums(start_date, end_date, amount)
        case 'tab-songs-summary' | _:
            t = init_songs(start_date, end_date, amount, sorted_by_minutes)

    # return songs, artists, albums
    return t
