import dash
import plotly.express as px
from dash import html, dcc, callback, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url
import dash_bootstrap_components as dbc

from analysis.graphics.webapp.helpers import dataframe_helpers
from analysis.graphics.webapp.helpers.consts import *
from analysis.graphics.webapp.helpers.df_filenames import *
from analysis.graphics.webapp.select_statements import *
from analysis.graphics.webapp.df_files import dataframe_loader, dataframe_getter

dash.register_page(__name__)

graph = dcc.Graph(
    id='single-song-bc'
)
"""
rbSelectionMethod = dcc.RadioItems(
    id='radio-items-ssong',
    options=[
        {'label': 'Song Name', 'value': 1},
        {'label': 'Song ID', 'value': 2}
    ],
    value='Song Name',
    labelStyle={'display': 'block'}
)
"""
rbSelectionMethod = html.Div(
    [
        dbc.RadioItems(
            id="radio-items-ssong",
            className="btn-group",
            inputClassName="btn-check",
            labelClassName="btn btn-outline-primary",
            labelCheckedClassName="active",
            options=[
                {"label": "Song Name", "value": 1},
                {"label": "Song ID", "value": 2},
            ],
            value=1,
        )
    ],
    className="radio-group",
)

t_song_name = dbc.Input(type='text',
                        id='inp-song-name',
                        placeholder="Insert Song here...",
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

layout = html.Div(children=[
    html.H1(children='Single Song Streams'),
    t_song_name,
    t_limit,
    html.Br(),
    rbSelectionMethod,
    html.Br(),
    dcc.Loading(
        id='load-single-song',
        children=[graph],
    ),
])

"""
html.Div(children=[
        html.Div(
            children=[
                rbSelectionMethod,
            ]
        ),
        html.Div(children=[
            dcc.Input(type='text', id='inp-song-name'),
        ]),
        html.Div(children=[
            dcc.Input(type='number', id='inp-limit', value=20),
        ]),
    ], style={
        'padding': '20px',
    }
    ),
"""


@callback(
    Output('single-song-bc', 'figure'),
    Input('inp-song-name', 'value'),
    Input('inp-limit', 'value'),
    Input('radio-items-ssong', 'value'),
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value"),
)
def update_graph(s_name, limit, rbvalue, theme):
    df_combined = dataframe_getter.get_top_song_df()

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
