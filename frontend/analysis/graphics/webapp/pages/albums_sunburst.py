import dash
import pandas as pd
import plotly.express as px
from dash import html, dcc, callback, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

from frontend.analysis.graphics.webapp.df_files import ndf_helper
from frontend.analysis.graphics.webapp.helpers.consts import *

dash.register_page(__name__)

graph = dcc.Graph(
    id='albums-sunburst'
)

layout = html.Div(children=[
    html.H1(children='Album Streams'),
    dcc.Loading(
        id='load-sb-album', children=[graph]
    )
])


@callback(
    Output('albums-sunburst', 'figure'),
    Input(DATAFRAME_STORE_ID, 'data'),
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value")
)
def update_graph_theme(df_store, theme):
    df = pd.DataFrame(df_store)
    df_combined = ndf_helper.get_top_songs_df(df)
    # df_combined = dataframe_getter.get_top_song_df()
    fig = px.sunburst(df_combined.head(n=1000), path=['Album', 'Song'], values='Stream Count',
                      title='Anzahl der Album-Streams nach Alben',
                      color='Stream Count', color_continuous_scale=default_color_scale,
                      template=template_from_url(theme),
                      height=1000
                      )
    return fig
