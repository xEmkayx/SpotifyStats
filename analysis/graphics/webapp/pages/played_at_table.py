import dash
import dash_bootstrap_components as dbc
from aio import ThemeChangerAIO
from dash import html, dcc, callback, Input, Output

from analysis.graphics.webapp.helpers import dataframe_helpers
from analysis.graphics.webapp.helpers.time_functions import *

from analysis.graphics.webapp.helpers.df_filenames import *
from analysis.graphics.webapp.select_statements import *
from analysis.graphics.webapp.df_files import dataframe_loader, dataframe_getter
from analysis.graphics.webapp.helpers.consts import *

dash.register_page(__name__)

"""
df = dataframe_getter.get_default_df()
theme_change = ThemeChangerAIO(aio_id="theme")

gr = df.groupby('Played at').agg(
    {'Song-ID': 'first', 'Song': 'first', 'Artist': ', '.join, 'Artist-ID': ', '.join,
     'Album': 'first', 'Album-ID': 'first'})

gr = gr.reset_index()[::-1]
"""

datepicker = dcc.DatePickerRange(
    id='played-at-table-date-picker',
    min_date_allowed=date(2010, 1, 1),
    max_date_allowed=TOMORROW_DATE,  # date(2022, 12, 12),  #
    initial_visible_month=date.today(),  # date(2022, 11, 1),  #
    end_date=TOMORROW_DATE,
    start_date=date(datetime.now().year, 1, 1)
)

button_7d = dbc.Button(
    'Letzte 7 Tage',
    id='played-at-table-button-7d-s-minutes',
    outline=True,
    color='primary',
    n_clicks=0
)

button_month = dbc.Button(
    'Letzter Monat',
    id='played-at-table-button-month-s-minutes',
    outline=True,
    color='primary',
    n_clicks=0
)

button_year = dbc.Button(
    'Letztes Jahr',
    id='played-at-table-button-year-s-minutes',
    outline=True,
    color='primary',
    n_clicks=0
)

buttons = dbc.ButtonGroup(
    id='btn-group-played-at-table',
    children=[
        button_7d,
        button_month,
        button_year
    ]
)

hoerzeit = html.Div(
    id='hoerzeit-table'
)

stream_count = html.Div(
    id='stream-count-table'
)

hz_neu = html.Center(
    html.Div(
        id='hz-table',
        className='hz-container',
        children=[
            html.Div(
                className='date',
                id='sm-days-table'
            ),
            html.Label('D', className='date-text'),
            html.Div(
                className='date',
                id='hours-sm-table'
            ),
            html.Label('H', className='date-text'),
            html.Div(
                className='date',
                id='sm-minutes-table'
            ),
            html.Label('M', className='date-text'),
            html.Div(
                className='date',
                id='sm-seconds-table'
            ),
            html.Label('S', className='date-text', style={'margin-right': '10px'}),
        ]

    )
)

# table = dbc.Table.from_dataframe(gr.head(n=1000), striped=True, bordered=True, hover=True)
table = dbc.Table(id='played-at-table-table')
layout = html.Div(
    [
        html.H1(
            ['Stream History']
        ),
        datepicker,
        html.Br(),
        buttons,
        html.Br(),
        hoerzeit,
        stream_count,
        hz_neu,
        table,
    ]
)


@callback(
    Output('played-at-table-date-picker', 'start_date'),
    Output('played-at-table-date-picker', 'end_date'),
    Output('played-at-table-button-7d-s-minutes', 'n_clicks'),
    Output('played-at-table-button-month-s-minutes', 'n_clicks'),
    Output('played-at-table-button-year-s-minutes', 'n_clicks'),

    [Input("played-at-table-button-7d-s-minutes", "n_clicks"),
     Input('played-at-table-button-month-s-minutes', 'n_clicks'),
     Input('played-at-table-button-year-s-minutes', 'n_clicks')
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
    Output('played-at-table-table', 'children'),
    Output('hoerzeit-table', 'children'),
    Output('stream-count-table', 'children'),
    Output('sm-days-table', 'children'),
    Output('hours-sm-table', 'children'),
    Output('sm-minutes-table', 'children'),
    Output('sm-seconds-table', 'children'),

    Input('played-at-table-date-picker', 'start_date'),
    Input('played-at-table-date-picker', 'end_date'),
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value")
)
def update_graph_theme(start_date, end_date, theme):
    df = dataframe_helpers.get_played_at_table(start_date=start_date, end_date=end_date)
    """
    df['Played at'] = pd.to_datetime(df['Played at'], format='%Y-%m-%d %H:%M')
    print('played at df:')
    print(df.head(n=5).to_string())

    mask = (df['Played at'] >= start_date) & (df['Played at'] <= end_date)
    # print(f'mask: {mask}')

    ndf = df.loc[mask]
    # print('ndf:')
    # print(ndf.head(n=5).to_string())
    """
    stream_sum = pd.to_timedelta('00:' + df["Song Length"]).sum()
    sum_conv = strfdelta(stream_sum, "{days} Tage, {hours} Stunden, {minutes} Minuten und {seconds} Sekunden")
    sum_text = f'(Ungefähre) Gesamte Hörzeit: {sum_conv}'
    sc_text = f'Anzahl Streams: {df.shape[0]}'
    days = strfdelta(stream_sum, "{days}")
    hours = strfdelta(stream_sum, "{hours}")
    minutes = strfdelta(stream_sum, "{minutes}")
    seconds = strfdelta(stream_sum, "{seconds}")

    tab = dbc.Table.from_dataframe(df.head(n=1000), striped=True, bordered=True, hover=True)

    return tab, sum_text, sc_text, days, hours, minutes, seconds

"""
df = dataframe_getter.get_top_album_df()
mask = dataframe_helpers.date_mask(start_date=start_date, end_date=end_date)
ndf = df.loc[mask]

# ndf = dataframe_helpers.get_top_albums(start_date=start_date, end_date=end_date)

all_albums_plot = px.bar(ndf.head(n=amount), x='Album', y="Stream Count", height=1000,  # markers=True,
                         title='Top Albums Streams',
                         color='Stream Count', color_continuous_scale=default_color_scale,
                         custom_data=['Album', 'Stream Count', 'Artist', 'Album-ID', 'Artist-ID'],
                         template=template_from_url(theme)
                         )

all_albums_plot.update_traces(
    hovertemplate="<br>".join([
        "Album: %{customdata[0]}",
        "Stream Count: %{customdata[1]}",
        "Artist: %{customdata[2]}",
        "Album-ID: %{customdata[3]}",
        "Artist-ID: %{customdata[4]}",
    ])
)

all_albums_plot.update_xaxes(showgrid=True, gridwidth=1,  # gridcolor='LightPink'
                             )
return all_albums_plot
"""
