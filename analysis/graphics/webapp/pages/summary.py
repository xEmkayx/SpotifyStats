import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output, DiskcacheManager
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

from analysis.graphics.webapp.components.StreamSortSwitchButton import StreamSortSwitchButton
from analysis.graphics.webapp.components.create_playlist_button import CreatePlaylistButton
from analysis.graphics.webapp.components.selection_box import SelectionBox, B7D_NAME, BMONTH_NAME, BYEAR_NAME
from analysis.graphics.webapp.helpers import summary_helpers, name_helpers
from analysis.graphics.webapp.helpers.time_functions import *
from analysis.graphics.webapp.helpers import consts
from spotify_scripts import playlist_creator

dash.register_page(__name__)

_, onscreen_songs = summary_helpers.init_songs(onscreen_songs=[])

current_filename = name_helpers.get_current_file_name(__file__)
sb = SelectionBox(current_filename)
datepicker_id = sb.get_datepicker_id()
b_ids = sb.get_buttons_ids()
b7d_id = b_ids[B7D_NAME]
bmonth_id = b_ids[BMONTH_NAME]
byear_id = b_ids[BYEAR_NAME]
input_id = sb.get_input_id()

streamed_by_buttons = StreamSortSwitchButton(current_filename)
streamed_by_buttons_id = streamed_by_buttons.get_id()

playlist_button = CreatePlaylistButton(current_filename)
playlist_button_id = playlist_button.get_id()

tabs = dbc.Tabs(
    children=[
        dbc.Tab(label='Songs', tab_id='tab-songs-summary'),
        dbc.Tab(label='Artists', tab_id='tab-artists-summary'),
        dbc.Tab(label='Albums', tab_id='tab-albums-summary'),
    ],
    # parent_className='custom-tabs',
    className='custom-tabs-container',
    id='summary-tabs',
    # value='tab-songs-summary'
    active_tab='tab-songs-summary',
    style={"marginBottom": "20px"}
)

content = html.Div(
    id='summary-content-div',
    className='summary-content-div'
)

layout = html.Div(children=[
    html.H1(children='Summary'),
    sb.render(),
    # html.Br(),
    streamed_by_buttons.render(),
    playlist_button.render(),
    tabs,
    content
])


@callback(
    Output(playlist_button_id, 'n_clicks'),
    [Input(playlist_button_id, 'n_clicks'),
     Input(datepicker_id, 'start_date'),
     Input(datepicker_id, 'end_date'),
     ],
)
def create_playlist_buttonclick(n_clicks, start_date, end_date):
    if n_clicks is not None and n_clicks > 0:
        # print(f'Length of onscreen songs: {len(onscreen_songs)}\nonscreen_songs:')
        # print(onscreen_songs.sort())
        playlist_creator.create_playlist(song_ids=onscreen_songs, range=f'{start_date} - {end_date}')


@callback(
    Output(datepicker_id, 'start_date'),
    Output(datepicker_id, 'end_date'),
    Output(b7d_id, 'n_clicks'),
    Output(bmonth_id, 'n_clicks'),
    Output(byear_id, 'n_clicks'),

    [Input(b7d_id, "n_clicks"),
     Input(bmonth_id, 'n_clicks'),
     Input(byear_id, 'n_clicks')
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

    [Input(datepicker_id, 'start_date'),
     Input(datepicker_id, 'end_date'),
     Input(input_id, 'value'),
     Input(streamed_by_buttons_id, "value"),
     # Input('summary-tabs', 'value')
     Input('summary-tabs', 'active_tab')
     ],
)
def update_tabs(start_date, end_date, amount, radio_values, selected_tab):
    sorted_by_minutes = False
    if radio_values == 1:
        sorted_by_minutes = False
    else:
        sorted_by_minutes = True

    global onscreen_songs

    match selected_tab:
        case 'tab-artists-summary':
            t = summary_helpers.init_artists(start_date, end_date, amount)
        case 'tab-albums-summary':
            t = summary_helpers.init_albums(start_date, end_date, amount)
        case 'tab-songs-summary' | _:
            t, onscreen_songs = summary_helpers.init_songs(start_date, end_date, amount, sorted_by_minutes)

    # return songs, artists, albums
    return t
