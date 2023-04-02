import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import html, dcc, callback, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

from analysis.graphics.webapp.helpers.df_filenames import *
# import datetime as dt
from analysis.graphics.webapp.helpers.time_functions import *
from analysis.graphics.webapp.select_statements import *
from analysis.graphics.webapp.helpers.summary_helpers import date_mask, normalize_to_minutes
from analysis.graphics.webapp.df_files import dataframe_loader

dash.register_page(__name__)

# df = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')
df = dataframe_loader.get_default_dataframe()

graph = dcc.Graph(
    id='stream-minutes-plot',
)

# TODO: MORGENS/ABENDS
tommorow = date(datetime.now().year, datetime.now().month, datetime.now().day + 1)

datepicker = dcc.DatePickerRange(
    id='stream-minutes-date-picker-minutes',
    min_date_allowed=date(2010, 1, 1),
    max_date_allowed=tommorow,  # date(2022, 12, 12),  #
    initial_visible_month=date.today(),  # date(2022, 11, 1),  #
    end_date=tommorow,
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

tabelle = dbc.Table.from_dataframe(df.head(n=100), striped=True, bordered=True, hover=True, id='tab-s-minutes')

tab_normal = dbc.Tab(
    [
        dcc.Loading(
            id='load-s-minutes',
            children=[graph],
        ),
    ],
    label='Graph',
)

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
        tab_tabelle
    ],
    parent_className='custom-tabs',
    className='custom-tabs-container',
)

layout = html.Div(children=[
    html.H1(children='Top Song streams in range'),
    datepicker,
    html.Br(),
    buttons,
    hoerzeit,
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
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value"),
    Input('stream-minutes-date-picker-minutes', 'start_date'),
    Input('stream-minutes-date-picker-minutes', 'end_date'),
    [  # Input('btn-group', 'submit'),
        Input("stream-minutes-button-7d-s-minutes", "n_clicks"),
        Input('stream-minutes-button-month-s-minutes', 'n_clicks'),
        Input('stream-minutes-button-year-s-minutes', 'n_clicks')
    ]
)
def update_graph_theme(theme, start_date, end_date, btn_7d, btn_m, btn_y):
    btn_7d = btn_m = btn_y = 0

    # mask = (df['Gespielt am'] > start_date) & (df['Gespielt am'] <= end_date)
    mask = date_mask(start_date, end_date)
    ndf = df.loc[mask]

    stream_sum = pd.to_timedelta('00:' + ndf["Songlänge"]).sum()
    sum_conv = strfdelta(stream_sum, "{days} Tage, {hours} Stunden, {minutes} Minuten und {seconds} Sekunden")
    sum_text = f'(Ungefähre) Gesamte Hörzeit: {sum_conv}'
    days = strfdelta(stream_sum, "{days}")
    hours = strfdelta(stream_sum, "{hours}")
    minutes = strfdelta(stream_sum, "{minutes}")
    seconds = strfdelta(stream_sum, "{seconds}")

    df_combined = normalize_to_minutes(ndf)

    fig = px.line(df_combined.head(n=100), x="Song", y="Streamed Mins", template=template_from_url(theme),
                  markers=True, height=1000,
                  # title=f'Streamzahlen aller Artist"',
                  custom_data=['Song', 'Anzahl Streams', 'Song-ID', 'Artist', 'Artist-ID', 'Album', 'Album-ID',
                               'Streamed Mins'])

    fig.update_traces(
        hovertemplate="<br>".join([
            "Song: %{customdata[0]}",
            "Anzahl Streams: %{customdata[1]}",
            "Streamed Mins: %{customdata[7]}",
            "Song-ID: %{customdata[2]}",
            "Artist: %{customdata[3]}",
            "Artist-ID: %{customdata[4]}",
            "Album: %{customdata[5]}",
            "Album-ID: %{customdata[6]}",
        ])
    )
    return fig, sum_text, days, hours, minutes, seconds


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
)
def update_table(start_date, end_date):
    # mask = (df['Gespielt am'] > start_date) & (df['Gespielt am'] <= end_date)
    mask = date_mask(start_date, end_date)
    ndf = df.loc[mask]

    df_combined = normalize_to_minutes(ndf)
    """
    gr = ndf.groupby('Gespielt am').agg(
        {'Song-ID': 'first', 'Song': 'first', 'Artist': ', '.join, 'Artist-ID': ', '.join,
         'Album': 'first', 'Album-ID': 'first'})

    counted = gr.value_counts('Song-ID').rename({1: 'Song-ID', 2: 'Anzahl Streams'}).sort_index().reset_index()
    counted.set_axis(['Song-ID', 'Anzahl Streams'], axis=1, inplace=True)
    rest = gr.reset_index().drop('Gespielt am', axis=1).drop_duplicates('Song-ID').sort_values('Song-ID')
    df_combined = pd.merge(counted, rest).sort_values('Anzahl Streams', ascending=False)
    """

    tab = dbc.Table.from_dataframe(df_combined.head(n=1000), striped=True, bordered=True, hover=True)
    return tab
