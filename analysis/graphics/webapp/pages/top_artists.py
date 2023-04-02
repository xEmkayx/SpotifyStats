import dash
import plotly.express as px
from dash import html, dcc, callback, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

from analysis.graphics.webapp.df_files import dataframe_loader
from analysis.graphics.webapp.helpers.time_functions import *
import dash_bootstrap_components as dbc
from analysis.graphics.webapp.helpers import summary_helpers
from analysis.graphics.webapp.helpers.consts import *

dash.register_page(__name__)

# df = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')
# df = dataframe_loader.get_default_dataframe()

tomorrow = date(datetime.now().year, datetime.now().month, datetime.now().day + 1)

datepicker = dcc.DatePickerRange(
    id='top-artists-date-picker',
    min_date_allowed=date(2010, 1, 1),
    max_date_allowed=tomorrow,  # date(2022, 12, 12),  #
    initial_visible_month=date.today(),  # date(2022, 11, 1),  #
    end_date=tomorrow,
    start_date=date(datetime.now().year, 1, 1)
)
"""
gr = df.groupby(['Artist', 'Artist-ID'], as_index=False).size()
df_sorted = gr.sort_values(by=['size'], ascending=False)
df_sorted.rename({1:'Artist', 2:'Artist-ID', 3:'Stream Count'})
df_sorted.set_axis(['Artist', 'Artist-ID', 'Stream Count'], axis=1, inplace=True)
"""

theme_change = ThemeChangerAIO(aio_id="theme")

button_7d = dbc.Button(
    'Letzte 7 Tage',
    id='top-artists-button-7d-s-minutes',
    outline=True,
    color='primary',
    n_clicks=0
)

button_month = dbc.Button(
    'Letzter Monat',
    id='top-artists-button-month-s-minutes',
    outline=True,
    color='primary',
    n_clicks=0
)

button_year = dbc.Button(
    'Letztes Jahr',
    id='top-artists-button-year-s-minutes',
    outline=True,
    color='primary',
    n_clicks=0
)

buttons = dbc.ButtonGroup(
    id='btn-group-top-artists',
    children=[
        button_7d,
        button_month,
        button_year
    ]
)

graph = dcc.Graph(
    id='all-artists-line',
    # figure=all_artists_plot
)

amount_tb = dbc.Input(
    id='inp-amount-top-artists',
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
    html.H1(children='All Artist Streams'),
    datepicker,
    amount_tb,
    html.Br(),
    buttons,
    dcc.Loading(
        id='load-top-artists',
        children=[graph],
    ),
    # theme_change
])


@callback(
    Output('top-artists-date-picker', 'start_date'),
    Output('top-artists-date-picker', 'end_date'),
    Output('top-artists-button-7d-s-minutes', 'n_clicks'),
    Output('top-artists-button-month-s-minutes', 'n_clicks'),
    Output('top-artists-button-year-s-minutes', 'n_clicks'),

    [Input("top-artists-button-7d-s-minutes", "n_clicks"),
     Input('top-artists-button-month-s-minutes', 'n_clicks'),
     Input('top-artists-button-year-s-minutes', 'n_clicks')
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
    Output("all-artists-line", "figure"),

    Input('top-artists-date-picker', 'start_date'),
    Input('top-artists-date-picker', 'end_date'),
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value"),
    Input('inp-amount-top-artists', 'value')
)
def update_graph_theme(start_date, end_date, theme, amount):
    ndf = summary_helpers.get_top_artists(start_date=start_date, end_date=end_date)

    fig = px.bar(ndf.head(n=amount), x='Artist', y="Stream Count", height=1000,
                 title='Top Artist Streams',
                 color='Stream Count', color_continuous_scale=default_color_scale,
                 custom_data=['Artist', 'Stream Count', 'Artist-ID'],
                 template=template_from_url(theme)
                 )
    """
    # fig = px.line(df_sorted.head(n=500), x="Artist", y="Stream Count", template=template_from_url(theme),
    fig = px.line(ndf.head(n=250), x="Artist", y="Stream Count", template=template_from_url(theme),
                  markers=True, height=1000,
                  title=f'Streamzahlen aller Artist"',
                  custom_data=['Artist', 'Stream Count', 'Artist-ID'])
    """

    fig.update_traces(
        hovertemplate="<br>".join([
            "Artist: %{customdata[0]}",
            "Stream Count: %{customdata[1]}",
            "Artist-ID: %{customdata[2]}",
        ])
    )
    return fig
