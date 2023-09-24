import dash
import dash_bootstrap_components as dbc
import plotly.express as px
from dash import html, dcc, callback, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

from analysis.graphics.webapp.components.streamed_time import StreamedTime
from analysis.graphics.webapp.helpers.time_functions import *
from analysis.graphics.webapp.select_statements import *
from analysis.graphics.webapp.helpers import dataframe_helpers
from analysis.graphics.webapp.df_files import dataframe_loader, dataframe_getter
from analysis.graphics.webapp.helpers.consts import *
from analysis.graphics.webapp.components.StreamSortSwitchButton import StreamSortSwitchButton
from analysis.graphics.webapp.components.create_playlist_button import CreatePlaylistButton
from analysis.graphics.webapp.components.selection_box import SelectionBox, B7D_NAME, BMONTH_NAME, BYEAR_NAME
from analysis.graphics.webapp.helpers import summary_helpers, name_helpers

dash.register_page(__name__)

# df = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')
# df = dataframe_loader.get_default_dataframe()
graph = dcc.Graph(
    id='stream-minutes-plot',
)

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

streamed_time = StreamedTime(current_filename)

"""
TODO: Tabelle wieder implementieren
tabelle = dbc.Table(id='tab-s-minutes').from_dataframe(df.head(n=100), 
striped=True, bordered=True, hover=True, id='tab-s-minutes')
"""

tab_normal = dbc.Tab(
    [
        dcc.Loading(
            id='load-s-minutes',
            children=[graph],
        ),
    ],
    label='Graph',
)

"""
tab_tabelle = dbc.Tab(
    [
        dcc.Loading(
            [tabelle],
            id='load-s-minutes-tab'
        )
    ],
    label='Tabelle',
    # selected_className='custom-tab--selected',
)

tabs = dcc.Tabs(
    [
        tab_normal,
        # tab_tabelle
    ],
    parent_className='custom-tabs',
    className='custom-tabs-container',
)
"""

tabs = dbc.Tabs(
    [
        tab_normal,
        # tab_tabelle
    ],
    # parent_className='custom-tabs',
    className='custom-tabs-container',
)

layout = html.Div(children=[
    html.H1(children='Top Song streams in range'),
    sb.render(),
    streamed_by_buttons.render(),
    streamed_time.render(),
    tabs
])


@callback(
    Output("stream-minutes-plot", "figure"),
    Output(streamed_time.stream_time_text_id, 'children'),
    Output(streamed_time.days_id, 'children'),
    Output(streamed_time.hours_id, 'children'),
    Output(streamed_time.minutes_id, 'children'),
    Output(streamed_time.seconds_id, 'children'),
    Output(streamed_time.total_streams_id, 'children'),

    [  # Input('btn-group', 'submit'),
        Input(ThemeChangerAIO.ids.radio("all-themes"), "value"),
        Input(datepicker_id, 'start_date'),
        Input(datepicker_id, 'end_date'),
        Input(b7d_id, "n_clicks"),
        Input(bmonth_id, 'n_clicks'),
        Input(byear_id, 'n_clicks'),
        Input(streamed_by_buttons_id, "value"),
        Input(input_id, 'value')
    ],
)
def update_graph_theme(theme, start_date, end_date, btn_7d, btn_m, btn_y, radio_values, amount):
    btn_7d = btn_m = btn_y = 0
    custom_data = ['Song', 'Stream Count', 'Song-ID', 'Artist', 'Artist-ID', 'Album', 'Album-ID']

    sorted_by_minutes = False
    if radio_values == 1:
        sorted_by_minutes = False
        custom_data.append('Song Length')
        y_axis = 'Stream Count'
        hover_text = "<br>".join([
            "Song: %{customdata[0]}",
            "Stream Count: %{customdata[1]}",
            "Artist: %{customdata[3]}",
            "Album: %{customdata[5]}",
            "Song Length: %{customdata[7]}",
            "Song-ID: %{customdata[2]}",
            "Artist-ID: %{customdata[4]}",
            "Album-ID: %{customdata[6]}",
        ])
    else:
        sorted_by_minutes = True
        custom_data.append('Streamed Mins')
        y_axis = 'Streamed Mins'
        hover_text = "<br>".join([
            "Song: %{customdata[0]}",
            "Stream Count: %{customdata[1]}",
            "Streamed Mins: %{customdata[7]}",
            "Artist: %{customdata[3]}",
            "Album: %{customdata[5]}",
            "Song-ID: %{customdata[2]}",
            "Artist-ID: %{customdata[4]}",
            "Album-ID: %{customdata[6]}",
        ])
        # TODO: output der Methoden gettopsongsdf von helper und getter vergleichen; anzeigeprobleme nur bei
        # Methode von getter

    df_combined = dataframe_helpers.get_top_songs_df(start_date=start_date, end_date=end_date,
                                                     sorted_by_mins=sorted_by_minutes)

    stream_sum = pd.to_timedelta('00:' + df_combined["Song Length"]).sum()
    sum_conv = strfdelta(stream_sum, "{days} Tage, {hours} Stunden, {minutes} Minuten und {seconds} Sekunden")
    sum_text = f'(Ungefähre) Gesamte Hörzeit: {sum_conv}'

    days = strfdelta(stream_sum, "{days}")
    hours = strfdelta(stream_sum, "{hours}")
    minutes = strfdelta(stream_sum, "{minutes}")
    seconds = strfdelta(stream_sum, "{seconds}")
    streams_text = f'Total Streams: {df_combined.shape[0]}'

    """
    fig = px.line(df_combined.head(n=amount), x="Song", y=y_axis,
                  template=template_from_url(theme),
                  markers=True, height=1000,
                  # title=f'Streamzahlen aller Artist"',
                  custom_data=custom_data)
    """

    fig = px.bar(df_combined.head(amount), x='Song', y=y_axis, height=850,
                 title='Top Song Streams',
                 color='Stream Count',
                 # color_continuous_scale=default_color_scale,
                 custom_data=custom_data,
                 template=template_from_url(theme))

    fig.update_traces(hovertemplate=hover_text)
    return fig, sum_text, days, hours, minutes, seconds, streams_text


@callback(
    Output(datepicker_id, 'start_date'),
    Output(datepicker_id, 'end_date'),
    Output(b7d_id, 'n_clicks'),
    Output(bmonth_id, 'n_clicks'),
    Output(byear_id, 'n_clicks'),

    [Input(b7d_id, "n_clicks"),
     Input(bmonth_id, 'n_clicks'),
     Input(byear_id, 'n_clicks'),
     ]
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


"""
@callback(
    Output('tab-s-minutes', 'children'),
    # TODO:
    # Output('hoerzeit-minutes-sm', 'children'),
    # Output('sm-days', 'children'),
    # Output('hours-sm', 'children'),
    # Output('sm-minutes', 'children'),
    # Output('sm-seconds', 'children'),
    Input('stream-minutes-date-picker-minutes', 'start_date'),
    Input('stream-minutes-date-picker-minutes', 'end_date'),
    Input("songs-line-streamed-by-radios", "value"),
)
def update_table(start_date, end_date, radio_values):
    sorted_by_minutes = False
    if radio_values == 1:
        sorted_by_minutes = False
    else:
        sorted_by_minutes = True

    df_combined = dataframe_helpers.get_top_songs_df(start_date=start_date, end_date=end_date,
                                                     sorted_by_mins=sorted_by_minutes)

    tab = dbc.Table.from_dataframe(df_combined.head(n=1000), striped=True, bordered=True, hover=True)
    return tab
"""
