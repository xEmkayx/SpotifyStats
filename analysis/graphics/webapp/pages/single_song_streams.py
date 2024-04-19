import dash
import pandas as pd
import plotly.express as px
from dash import html, dcc, callback, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

from analysis.graphics.webapp.components.single_type_selection import SingleTypeSelection
from analysis.graphics.webapp.helpers.consts import *
from analysis.graphics.webapp.df_files import ndf_helper

dash.register_page(__name__)

graph = dcc.Graph(
    id='single-song-bc'
)

single_type_selection = SingleTypeSelection('song')
rb_selection_method_id = single_type_selection.rb_selection_method_id
input_name_id = single_type_selection.input_name_id
input_limit_id = single_type_selection.input_limit_id

# store = DataframeStore()

layout = html.Div(children=[
    html.H1(children='Single Song Streams'),
    single_type_selection.render(),
    html.Br(),
    dcc.Loading(
        id='load-single-song',
        children=[graph],
    ),
])


@callback(
    Output('single-song-bc', 'figure'),
    Input('store-dataframe', 'data'),
    Input(input_name_id, 'value'),
    Input(input_limit_id, 'value'),
    Input(rb_selection_method_id, 'value'),
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value"),
)
def update_graph(df_store, s_name, limit, rbvalue, theme):
    df = pd.DataFrame(df_store)
    df_combined = ndf_helper.get_top_songs_df(df)

    if rbvalue == 1:
        df_filter = 'Song'
    elif rbvalue == 2:
        df_filter = 'Song-ID'
    else:
        df_filter = 'Song'

    df_filtered = df_combined[df_combined[df_filter].str.contains(str(s_name), case=False)].head(n=limit)
    single_song_barchart = px.bar(df_filtered, y='Song', x='Stream Count',
                                  title=f'Songs, die "{s_name}" enthalten', height=1000,
                                  # text_auto='.2s',
                                  orientation='h',
                                  color='Stream Count', color_continuous_scale=default_color_scale,
                                  template=template_from_url(theme),
                                  custom_data=['Artist', 'Song', 'Stream Count', 'Album',
                                               'Artist-ID', 'Song-ID', 'Album-ID'])

    single_song_barchart.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
    single_song_barchart.update_layout(yaxis=dict(autorange="reversed"))

    single_song_barchart.update_layout(
        # plot_bgcolor=colors['background'],
        # paper_bgcolor=colors['background'],
        # font_color=colors['amaranth'],
        transition_duration=500
    )

    single_song_barchart.update_traces(
        hovertemplate="<br>".join([
            "Artist: %{customdata[0]}",
            "Song: %{customdata[1]}",
            "Album: %{customdata[3]}",
            "Streams: %{customdata[2]}",
            "Song-ID: %{customdata[5]}",
            "Artist-ID: %{customdata[4]}",
            "Album-ID: %{customdata[6]}",
        ])
    )

    return single_song_barchart
