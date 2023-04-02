import dash
import dash_bootstrap_components as dbc
import plotly.express as px
from dash import html, dcc, callback, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

from analysis.graphics.webapp.helpers.df_filenames import *
# import datetime
from analysis.graphics.webapp.helpers.time_functions import *
from analysis.graphics.webapp.select_statements import *

"""

dash.register_page(__name__)

df = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')

graph = dcc.Graph(
    id='played-at-plot',
)
"" "
    TODO: TIMELINE:
    graphen für jeden monat berechnen und als animation ausgeben
    
    rest hier anpassen; ist bisher 1:1 kopiert
"""

"""
datepicker = dcc.DatePickerRange(
    id='date-picker-range',
    min_date_allowed=date(2021, 1, 1),
    max_date_allowed=date(2022, 12, 12),  # date.today(),
    initial_visible_month=date(2022, 11, 1),  # date.today(),
    end_date=date(datetime.now().year, datetime.now().month, datetime.now().day + 1),
    start_date=date(datetime.now().year, 1, 1)
)

hoerzeit = html.Div(
    id='hoerzeit-pa-range'
)
hz_neu = html.Center(
    html.Div(
        id='hz',
        className='hz-container',
        children=[
            html.Div(
                className='date',
                id='days'
            ),
            html.Label('D', className='date-text'),
            html.Div(
                className='date',
                id='hours'
            ),
            html.Label('H', className='date-text'),
            html.Div(
                className='date',
                id='minutes'
            ),
            html.Label('M', className='date-text'),
            html.Div(
                className='date',
                id='seconds'
            ),
            html.Label('S', className='date-text', style={'margin-right': '10px'}),
        ]

    )
)

button_7d = dbc.Button(
    'Letzte 7 Tage',
    id='button-7d',
    outline=True,
    color='primary',
    n_clicks=0
)

button_month = dbc.Button(
    'Letzter Monat',
    id='button-month',
    outline=True,
    color='primary',
    n_clicks=0
)

button_year = dbc.Button(
    'Letztes Jahr',
    id='button-year',
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

toast = dbc.Toast(
    [html.P(f"Button pressed", className="mb-0")],
    header="Toast",
    # duration=4000,
    dismissable=True,
    id='toast1',
    icon="warning",
    is_open=False,
    style={"position": "fixed", "top": 66, "right": 10, "width": 350},
)

tabelle = dbc.Table.from_dataframe(df.head(n=100), striped=True, bordered=True, hover=True, id='tab-pa-range')

tab_normal = dbc.Tab(
    [
        dcc.Loading(
            id='load-pa-range',
            children=[graph],
        ),
    ],
    label='Graph',
)

tab_tabelle = dbc.Tab(
    [
        dcc.Loading(
            [tabelle],
            id='load-pa-range-tab'
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
    toast,
    html.H1(children='Top Song streams in range'),
    datepicker,
    html.Br(),
    buttons,
    hoerzeit,
    hz_neu,
    tabs
])


@callback(
    Output("played-at-plot", "figure"),
    Output('hoerzeit-pa-range', 'children'),
    Output('days', 'children'),
    Output('hours', 'children'),
    Output('minutes', 'children'),
    Output('seconds', 'children'),
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value"),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    [  # Input('btn-group', 'submit'),
        Input("button-7d", "n_clicks"),
        Input('button-month', 'n_clicks'),
        Input('button-year', 'n_clicks')
    ]
)
def update_graph_theme(theme, start_date, end_date, btn_7d, btn_m, btn_y):
    btn_7d = btn_m = btn_y = 0

    mask = (df['Gespielt am'] > start_date) & (df['Gespielt am'] <= end_date)
    ndf = df.loc[mask]

    sum = pd.to_timedelta('00:' + ndf["Songlänge"]).sum()
    sum_conv = strfdelta(sum, "{days} Tage, {hours} Stunden, {minutes} Minuten und {seconds} Sekunden")
    sum_text = f'(Ungefähre) Gesamte Hörzeit: {sum_conv}'
    days = strfdelta(sum, "{days}")
    hours = strfdelta(sum, "{hours}")
    minutes = strfdelta(sum, "{minutes}")
    seconds = strfdelta(sum, "{seconds}")

    gr = ndf.groupby('Gespielt am').agg(
        {'Song-ID': 'first', 'Song': 'first', 'Artist': ', '.join, 'Artist-ID': ', '.join,
         'Album': 'first', 'Album-ID': 'first'})

    counted = gr.value_counts('Song-ID').rename({1: 'Song-ID', 2: 'Anzahl Streams'}).sort_index().reset_index()
    counted.set_axis(['Song-ID', 'Anzahl Streams'], axis=1, inplace=True)
    rest = gr.reset_index().drop('Gespielt am', axis=1).drop_duplicates('Song-ID').sort_values('Song-ID')
    df_combined = pd.merge(counted, rest).sort_values('Anzahl Streams', ascending=False)

    fig = px.line(df_combined.head(n=100), x="Song", y="Anzahl Streams", template=template_from_url(theme),
                  markers=True, height=1000,
                  # title=f'Streamzahlen aller Artist"',
                  custom_data=['Song', 'Anzahl Streams', 'Song-ID', 'Artist', 'Artist-ID', 'Album', 'Album-ID'])

    fig.update_traces(
        hovertemplate="<br>".join([
            "Song: %{customdata[0]}",
            "Anzahl Streams: %{customdata[1]}",
            "Song-ID: %{customdata[2]}",
            "Artist: %{customdata[3]}",
            "Artist-ID: %{customdata[4]}",
            "Album: %{customdata[5]}",
            "Album-ID: %{customdata[6]}",
        ])
    )
    return fig, sum_text, days, hours, minutes, seconds


@callback(
    Output('date-picker-range', 'start_date'),
    Output('date-picker-range', 'end_date'),
    Output('button-7d', 'n_clicks'),
    Output('button-month', 'n_clicks'),
    Output('button-year', 'n_clicks'),

    [Input("button-7d", "n_clicks"),
     Input('button-month', 'n_clicks'),
     Input('button-year', 'n_clicks')
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
    Output('tab-pa-range', 'children'),
    # TODO:
    # Output('hoerzeit-pa-range', 'children'),
    # Output('days', 'children'),
    # Output('hours', 'children'),
    # Output('minutes', 'children'),
    # Output('seconds', 'children'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
)
def update_table(start_date, end_date):
    mask = (df['Gespielt am'] > start_date) & (df['Gespielt am'] <= end_date)
    ndf = df.loc[mask]

    gr = ndf.groupby('Gespielt am').agg(
        {'Song-ID': 'first', 'Song': 'first', 'Artist': ', '.join, 'Artist-ID': ', '.join,
         'Album': 'first', 'Album-ID': 'first'})

    counted = gr.value_counts('Song-ID').rename({1: 'Song-ID', 2: 'Anzahl Streams'}).sort_index().reset_index()
    counted.set_axis(['Song-ID', 'Anzahl Streams'], axis=1, inplace=True)
    rest = gr.reset_index().drop('Gespielt am', axis=1).drop_duplicates('Song-ID').sort_values('Song-ID')
    df_combined = pd.merge(counted, rest).sort_values('Anzahl Streams', ascending=False)

    tab = dbc.Table.from_dataframe(df_combined.head(n=1000), striped=True, bordered=True, hover=True)
    return tab
"""
