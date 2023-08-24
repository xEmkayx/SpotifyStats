import dash
import plotly.express as px
from dash import html, dcc, callback, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

from analysis.graphics.webapp.df_files import dataframe_getter
from analysis.graphics.webapp.helpers.consts import *
from analysis.graphics.webapp.helpers.time_functions import *
import dash_bootstrap_components as dbc
from analysis.graphics.webapp.helpers import dataframe_helpers

dash.register_page(__name__)

graph = dcc.Graph(
    id='album-streams-line'
)

theme_change = ThemeChangerAIO(aio_id="theme")

tomorrow = date(datetime.now().year, datetime.now().month, datetime.now().day + 1)

datepicker = dcc.DatePickerRange(
    id='top-albums-date-picker',
    min_date_allowed=date(2010, 1, 1),
    max_date_allowed=tomorrow,  # date(2022, 12, 12),  #
    initial_visible_month=date.today(),  # date(2022, 11, 1),  #
    end_date=tomorrow,
    start_date=date(datetime.now().year, 1, 1)
)

button_7d = dbc.Button(
    'Letzte 7 Tage',
    id='top-albums-button-7d-s-minutes',
    outline=True,
    color='primary',
    n_clicks=0
)

button_month = dbc.Button(
    'Letzter Monat',
    id='top-albums-button-month-s-minutes',
    outline=True,
    color='primary',
    n_clicks=0
)

button_year = dbc.Button(
    'Letztes Jahr',
    id='top-albums-button-year-s-minutes',
    outline=True,
    color='primary',
    n_clicks=0
)

buttons = dbc.ButtonGroup(
    id='btn-group-top-albums',
    children=[
        button_7d,
        button_month,
        button_year
    ]
)

amount_tb = dbc.Input(
    id='inp-amount-top-albums',
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
    html.H1(children='Album Streams'),
    datepicker,
    amount_tb,
    html.Br(),
    buttons,
    dcc.Loading(
        id='load-top-albums',
        children=[graph]
    ),
])


@callback(
    Output('top-albums-date-picker', 'start_date'),
    Output('top-albums-date-picker', 'end_date'),
    Output('top-albums-button-7d-s-minutes', 'n_clicks'),
    Output('top-albums-button-month-s-minutes', 'n_clicks'),
    Output('top-albums-button-year-s-minutes', 'n_clicks'),

    [Input("top-albums-button-7d-s-minutes", "n_clicks"),
     Input('top-albums-button-month-s-minutes', 'n_clicks'),
     Input('top-albums-button-year-s-minutes', 'n_clicks')
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
    Output('album-streams-line', 'figure'),

    Input('top-albums-date-picker', 'start_date'),
    Input('top-albums-date-picker', 'end_date'),
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value"),
    Input('inp-amount-top-albums', 'value')
)
def update_graph_theme(start_date, end_date, theme, amount):
    # df = dataframe_getter.get_top_album_df()
    # mask = dataframe_helpers.date_mask(start_date=start_date, end_date=end_date)
    # ndf = df.loc[mask]

    ndf = dataframe_helpers.get_top_albums(start_date=start_date, end_date=end_date)

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
