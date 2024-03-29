import dash
import plotly.express as px
from dash import html, dcc, callback, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

from analysis.graphics.webapp.helpers.consts import *
from analysis.graphics.webapp.df_files import dataframe_getter

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
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value")
)
def update_graph_theme(theme):
    # df_combined = dataframe_helpers.get_top_songs_df()
    df_combined = dataframe_getter.get_top_song_df()
    fig = px.sunburst(df_combined.head(n=1000), path=['Album', 'Song'], values='Stream Count',
                      title='Anzahl der Album-Streams nach Alben',
                      color='Stream Count', color_continuous_scale=default_color_scale,
                      template=template_from_url(theme),
                      height=1000
                      )
    return fig
