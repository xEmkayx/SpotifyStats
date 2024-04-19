import dash
import plotly.express as px
from dash import html, dcc, callback, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

from analysis.graphics.webapp.components.single_type_selection import SingleTypeSelection
from analysis.graphics.webapp.helpers.consts import *
from analysis.graphics.webapp.select_statements import *
from analysis.graphics.webapp.df_files import ndf_helper

dash.register_page(__name__)

graph = dcc.Graph(
    id='single-artists-line'
)

single_type_selection = SingleTypeSelection('artist')
rb_selection_method_id = single_type_selection.rb_selection_method_id
input_name_id = single_type_selection.input_name_id
input_limit_id = single_type_selection.input_limit_id

layout = html.Div(children=[
    html.H1(children='Single Artist Streams'),
    single_type_selection.render(),
    html.Br(),
    dcc.Loading(
        id='load-single-artists',
        children=[graph],
    ),
])


@callback(
    Output('single-artists-line', 'figure'),
    Input(DATAFRAME_STORE_ID, 'data'),
    Input(input_name_id, 'value'),
    Input(input_limit_id, 'value'),
    Input(rb_selection_method_id, 'value'),
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value"),
)
def update_graph(df_store, artist, limit, rbvalue, theme):
    artist = str(artist)
    # df_combined = dataframe_helpers.get_top_songs_df()
    df = pd.DataFrame(df_store)
    df_combined = ndf_helper.get_top_songs_df(df)
    # df_combined = dataframe_getter.get_top_song_df()

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
