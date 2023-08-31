import dash
import dash_bootstrap_components as dbc
import plotly.express as px
from dash import html, dcc, callback, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

from analysis.graphics.webapp.helpers.time_functions import *
from analysis.graphics.webapp.select_statements import *
from analysis.graphics.webapp.helpers import dataframe_helpers
from analysis.graphics.webapp.df_files import dataframe_loader, dataframe_getter
from analysis.graphics.webapp.helpers.consts import *

dash.register_page(__name__)

# df = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')
# df = dataframe_loader.get_default_dataframe()
graph = dcc.Graph(
    id='stream-minutes-plot',
)

# TODO: MORGENS/ABENDS

datepicker = dcc.DatePickerRange(
    id='stream-minutes-date-picker-minutes',
    min_date_allowed=date(2010, 1, 1),
    max_date_allowed=TOMORROW_DATE,  # date(2022, 12, 12),  #
    initial_visible_month=date.today(),  # date(2022, 11, 1),  #
    end_date=TOMORROW_DATE,
    start_date=date(datetime.now().year, 1, 1)
)

hoerzeit = html.Div(
    id='hoerzeit-minutes-sm'
)
hz_neu = html.Center(
    html.Div(
        id='hz',
        className='hz-container',
        children=[
            html.Div(
                className='date',
                id='sm-days'
            ),
            html.Label('D', className='date-text'),
            html.Div(
                className='date',
                id='hours-sm'
            ),
            html.Label('H', className='date-text'),
            html.Div(
                className='date',
                id='sm-minutes'
            ),
            html.Label('M', className='date-text'),
            html.Div(
                className='date',
                id='sm-seconds'
            ),
            html.Label('S', className='date-text', style={'margin-right': '10px'}),
        ]

    )
)

total_streams = html.Div(
    id='total_streams-minutes-sm'
)

button_7d = dbc.Button(
    'Letzte 7 Tage',
    id='stream-minutes-button-7d-s-minutes',
    outline=True,
    color='primary',
    n_clicks=0
)

button_month = dbc.Button(
    'Letzter Monat',
    id='stream-minutes-button-month-s-minutes',
    outline=True,
    color='primary',
    n_clicks=0
)

button_year = dbc.Button(
    'Letztes Jahr',
    id='stream-minutes-button-year-s-minutes',
    outline=True,
    color='primary',
    n_clicks=0
)

buttons = dbc.ButtonGroup(
    id='btn-group',
    children=[
        button_7d,
        button_month,
        button_year
    ]
)
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
"""

tabs = dcc.Tabs(
    [
        tab_normal,
        # tab_tabelle
    ],
    parent_className='custom-tabs',
    className='custom-tabs-container',
)

streamed_by_buttons = html.Div(
    [
        dbc.RadioItems(
            id="songs-line-streamed-by-radios",
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

amount_tb = dbc.Input(
    id='inp-amount-top-songs',
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

layout = html.Div(children=[
    html.H1(children='Top Song streams in range'),
    datepicker,
    amount_tb,
    html.Br(),
    buttons,
    html.Br(),
    streamed_by_buttons,
    hoerzeit,
    # html.Br(),
    total_streams,
    hz_neu,
    tabs
])


@callback(
    Output("stream-minutes-plot", "figure"),
    Output('hoerzeit-minutes-sm', 'children'),
    Output('sm-days', 'children'),
    Output('hours-sm', 'children'),
    Output('sm-minutes', 'children'),
    Output('sm-seconds', 'children'),
    Output('total_streams-minutes-sm', 'children'),

    Input(ThemeChangerAIO.ids.radio("all-themes"), "value"),
    Input('stream-minutes-date-picker-minutes', 'start_date'),
    Input('stream-minutes-date-picker-minutes', 'end_date'),
    [  # Input('btn-group', 'submit'),
        Input("stream-minutes-button-7d-s-minutes", "n_clicks"),
        Input('stream-minutes-button-month-s-minutes', 'n_clicks'),
        Input('stream-minutes-button-year-s-minutes', 'n_clicks'),
        Input("songs-line-streamed-by-radios", "value")
    ],
    Input('inp-amount-top-songs', 'value')
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
                 color='Stream Count', color_continuous_scale=default_color_scale,
                 custom_data=custom_data,
                 template=template_from_url(theme))

    fig.update_traces(hovertemplate=hover_text)
    return fig, sum_text, days, hours, minutes, seconds, streams_text


@callback(
    Output('stream-minutes-date-picker-minutes', 'start_date'),
    Output('stream-minutes-date-picker-minutes', 'end_date'),
    Output('stream-minutes-button-7d-s-minutes', 'n_clicks'),
    Output('stream-minutes-button-month-s-minutes', 'n_clicks'),
    Output('stream-minutes-button-year-s-minutes', 'n_clicks'),

    [Input("stream-minutes-button-7d-s-minutes", "n_clicks"),
     Input('stream-minutes-button-month-s-minutes', 'n_clicks'),
     Input('stream-minutes-button-year-s-minutes', 'n_clicks')
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
