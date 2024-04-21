import dash
import plotly.express as px
from dash import html, dcc, callback, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

from frontend.analysis.graphics.webapp.helpers.consts import *
from frontend.analysis.graphics.webapp.select_statements import *
from frontend.analysis.graphics.webapp.df_files import ndf_helper

dash.register_page(__name__)

graph = dcc.Graph(
    id='multifunction-sunburst'
)


layout = html.Div(children=[
    html.H1(children='Artist-Album-Song Streams'),
    dcc.Loading(
        id='load-sb-songs',
        children=[graph],
    )
])


@callback(
    Output('multifunction-sunburst', 'figure'),
    Input(DATAFRAME_STORE_ID, 'data'),
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value"),
)
def update_graph_theme(df_store, theme):
    # df_combined = dataframe_helpers.get_top_songs_df()
    # df_combined = dataframe_getter.get_top_song_df()
    df = pd.DataFrame(df_store)
    df_combined = ndf_helper.get_top_songs_df(df)

    song_streams_plot = px.sunburst(df_combined.head(n=1000),
                                    path=['Artist', 'Album', 'Song'], values='Stream Count',
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
