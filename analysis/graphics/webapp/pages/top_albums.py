import dash
import pandas as pd
import plotly.express as px
from dash import html, dcc, callback, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

from analysis.graphics.webapp.components.selection_box import SelectionBox, B7D_NAME
from analysis.graphics.webapp.components.selection_box import B7D_NAME, BMONTH_NAME, BYEAR_NAME
from analysis.graphics.webapp.df_files import ndf_helper
from analysis.graphics.webapp.helpers.consts import *
from analysis.graphics.webapp.helpers.time_functions import *
import dash_bootstrap_components as dbc
from analysis.graphics.webapp.helpers import dataframe_helpers, name_helpers

dash.register_page(__name__)

graph = dcc.Graph(
    id='album-streams-line'
)

theme_change = ThemeChangerAIO(aio_id="theme")

sb = SelectionBox(name_helpers.get_current_file_name(__file__))
datepicker_id = sb.get_datepicker_id()
b_ids = sb.get_buttons_ids()
b7d_id = b_ids[B7D_NAME]
bmonth_id = b_ids[BMONTH_NAME]
byear_id = b_ids[BYEAR_NAME]
input_id = sb.get_input_id()

layout = html.Div(children=[
    html.H1(children='Album Streams'),
    sb.render(),
    dcc.Loading(
        id='load-top-albums',
        children=[graph]
    ),
])


@callback(
    Output(datepicker_id, 'start_date'),
    Output(datepicker_id, 'end_date'),
    Output(b7d_id, 'n_clicks'),
    Output(bmonth_id, 'n_clicks'),
    Output(byear_id, 'n_clicks'),

    [Input(b7d_id, "n_clicks"),
     Input(bmonth_id, 'n_clicks'),
     Input(byear_id, 'n_clicks')
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

    Input(DATAFRAME_STORE_ID, 'data'),
    Input(datepicker_id, 'start_date'),
    Input(datepicker_id, 'end_date'),
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value"),
    Input(input_id, 'value')
)
def update_graph_theme(df_store, start_date, end_date, theme, amount):
    df = pd.DataFrame(df_store)

    ndf = ndf_helper.get_top_songs_df(df, start_date=start_date, end_date=end_date)

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
