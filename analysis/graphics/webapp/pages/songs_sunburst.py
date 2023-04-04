import dash
import plotly.express as px
from dash import html, dcc, callback, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

from analysis.graphics.webapp.helpers.consts import *
from analysis.graphics.webapp.helpers.df_filenames import *
from analysis.graphics.webapp.select_statements import *
from analysis.graphics.webapp.df_files import dataframe_loader
from analysis.graphics.webapp.helpers import summary_helpers

dash.register_page(__name__)

graph = dcc.Graph(
    id='song-streams-sunburst'
)


layout = html.Div(children=[
    html.H1(children='Song Streams'),
    dcc.Loading(
        id='load-sb-songs',
        children=[graph],
    )
])


@callback(
    Output('song-streams-sunburst', 'figure'),
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value"),
)
def update_graph_theme(theme):
    df_combined = summary_helpers.get_top_songs_df()
    song_streams_plot = px.sunburst(df_combined.head(n=1000), path=['Artist', 'Song'], values='Stream Count',
                                    title='Anzahl aller Song Streams',
                                    color='Stream Count', color_continuous_scale=default_color_scale,
                                    template=template_from_url(theme),
                                    height=1000,
                                    custom_data=['Song', 'Stream Count', 'Song-ID', 'Artist', 'Artist-ID',
                                                 'Album', 'Album-ID'])

    # song_streams_plot.update_layout(
    #     plot_bgcolor=colors['background'],
    #     paper_bgcolor=colors['background'],
    #     font_color=colors['amaranth']
    # )

    song_streams_plot.update_traces(
        hovertemplate="<br>".join([
            "Song: %{customdata[0]}",
            "Stream Count: %{customdata[1]}",
            "Song-ID: %{customdata[2]}",
            "Artist: %{customdata[3]}",
            "Artist-ID(s): %{customdata[4]}",
            "Album: %{customdata[5]}",
            "Album-ID: %{customdata[6]}",
        ])
    )

    return song_streams_plot
