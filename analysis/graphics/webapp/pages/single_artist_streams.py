import dash
import plotly.express as px
from dash import html, dcc, callback, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

# from analysis.graphics.webapp.helpers import dataframe_helpers
from analysis.graphics.webapp.helpers.consts import *
from analysis.graphics.webapp.helpers.df_filenames import *
from analysis.graphics.webapp.select_statements import *
from analysis.graphics.webapp.df_files import dataframe_loader, dataframe_getter
import dash_bootstrap_components as dbc

dash.register_page(__name__)
# df_combined = dataframe_helpers.get_top_songs_df()
# df_combined = dataframe_helpers.get_top_songs_df()

rbSelectionMethod = html.Div(
    [
        dbc.RadioItems(
            id="radio-items-sart",
            className="btn-group",
            inputClassName="btn-check",
            labelClassName="btn btn-outline-primary",
            labelCheckedClassName="active",
            options=[
                {"label": "Artist Name", "value": 1},
                {"label": "Artist ID", "value": 2},
            ],
            value=1,
        )
    ],
    className="radio-group",
)

t_artist_name = dbc.Input(type='text',
                          id='inp-artist',
                          placeholder="Insert Artist here...",
                          style={
                              'width': '10%',
                              'margin-left': '5px',
                              'margin-right': '5px',
                              'display': 'inline-block',
                          }
                          )

t_limit = dbc.Input(type='number',
                    id='inp-limit',
                    value=20,
                    # className='inp-summary',
                    style={
                        'width': '4%',
                        'margin-left': '5px',
                        'margin-right': '5px',
                        'display': 'inline-block',
                    }
                    )

graph = dcc.Graph(
    id='single-artists-line'
)

layout = html.Div(children=[
    html.H1(children='Single Artist Streams'),
    t_artist_name,
    t_limit,
    html.Br(),
    rbSelectionMethod,
    html.Br(),
    dcc.Loading(
        id='load-single-artists',
        children=[graph],
    ),
])


@callback(
    Output('single-artists-line', 'figure'),
    Input('inp-artist', 'value'),
    Input('inp-limit', 'value'),
    Input('radio-items-sart', 'value'),
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value"),
)
def update_graph(artist, limit, rbvalue, theme):
    artist = str(artist)
    # df_combined = dataframe_helpers.get_top_songs_df()
    df_combined = dataframe_getter.get_top_song_df()

    # TODO: REGEX BUTTON
    if rbvalue == 1:
        df_filter = 'Artist'
    elif rbvalue == 2:
        df_filter = 'Artist-ID'
    else:
        df_filter = 'Artist'

    df_filtered = df_combined[df_combined[df_filter].str.contains(str(artist), case=False)].head(n=limit)
    single_artist_barchart = px.bar(df_filtered, y='Song', x='Stream Count',
                                    title=f'Songs von "{artist}"', height=1000,
                                    text_auto='.2s', orientation='h',
                                    color='Stream Count', color_continuous_scale=default_color_scale,
                                    template=template_from_url(theme),
                                    text='Song',
                                    custom_data=['Artist', 'Song', 'Stream Count'])
    single_artist_barchart.update_traces(textfont_size=12, textposition="inside")
    single_artist_barchart.update_layout(yaxis=dict(autorange="reversed"))

    single_artist_barchart.update_layout(
        # plot_bgcolor=colors['background'],
        # paper_bgcolor=colors['background'],
        # font_color=colors['amaranth'],
        transition_duration=500
    )

    single_artist_barchart.update_traces(
        hovertemplate="<br>".join([
            "Artist: %{customdata[0]}",
            "Song: %{customdata[1]}",
            "Streams: %{customdata[2]}"
        ])
    )

    # return single_artists_plot
    return single_artist_barchart
