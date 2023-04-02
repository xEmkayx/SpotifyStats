import dash
import plotly.express as px
from dash import html, dcc, callback, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url
import dash_bootstrap_components as dbc

from analysis.graphics.webapp.helpers.consts import *
from analysis.graphics.webapp.select_statements import *
from analysis.graphics.webapp.df_files import dataframe_loader

dash.register_page(__name__)

# df = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')
df = dataframe_loader.get_default_dataframe()

gr = df.groupby('Played at').agg(
    {'Song-ID': 'first', 'Song': 'first', 'Artist': ', '.join, 'Artist-ID': ', '.join,
     'Album': 'first', 'Album-ID': 'first'})

counted = gr.value_counts('Song-ID').rename({1: 'Song-ID', 2: 'Stream Count'}).sort_index().reset_index()
counted.set_axis(['Song-ID', 'Stream Count'], axis=1, inplace=True)

rest = gr.reset_index().drop('Played at', axis=1).drop_duplicates('Song-ID').sort_values('Song-ID')

df_combined = pd.merge(counted, rest).sort_values('Stream Count', ascending=False)

graph = dcc.Graph(
    id='single-albums-bar'
)

"""
rbSelectionMethod = dcc.RadioItems(
    id='radio-items-salbum',
    options=[
        {'label': 'Album Name', 'value': 1},
        {'label': 'Album ID', 'value': 2}
    ],
    value='Album Name',
    labelStyle={'display': 'block'},
    # className='radiobuttons'
)
"""

rbSelectionMethod = html.Div(
    [
        dbc.RadioItems(
            id="radio-items-salbum",
            className="btn-group",
            inputClassName="btn-check",
            labelClassName="btn btn-outline-primary",
            labelCheckedClassName="active",
            options=[
                {"label": "Album Name", "value": 1},
                {"label": "Album ID", "value": 2},
            ],
            value=1,
        )
    ],
    className="radio-group",
)

t_album_name = dbc.Input(type='text',
                         id='inp-album-name',
                         placeholder="Insert Album here...",
                         # className='inp-summary',
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
    html.H1(children='Single Album Streams'),
    t_album_name,
    t_limit,
    html.Br(),
    rbSelectionMethod,
    # dcc.Input(type='text', id='inp-album-name'),
    # dcc.Input(type='number', id='inp-limit', value=20),
    html.Br(),
    dcc.Loading(
        id='load-single-album',
        children=[graph],
    ),
])
"""
html.Div(className='container-single',
             children=[
                 html.Div(children=[
                     dcc.Input(type='text', id='inp-album-name'),
                 ]),
                 html.Div(children=[
                     dcc.Input(type='number', id='inp-limit', value=20),
                 ]),
             ],
             ),
    html.Div(
        # className='container-radiobuttons',
        children=[
            rbSelectionMethod,
        ]
    ),                 
"""

@callback(
    Output('single-albums-bar', 'figure'),
    Input('inp-album-name', 'value'),
    Input('inp-limit', 'value'),
    Input('radio-items-salbum', 'value'),
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value"),
)
def update_graph(alb_name, limit, rbvalue, theme):
    alb_name = str(alb_name)
    # TODO: REGEX BUTTON
    if rbvalue == 1:
        df_filtered = df_combined[df_combined['Album'].str.contains(str(alb_name), case=False)].head(n=limit)
    elif rbvalue == 2:
        df_filtered = df_combined[df_combined['Album-ID'].str.contains(str(alb_name), case=False)].head(n=limit)
    else:
        df_filtered = df_combined[df_combined['Album'].str.contains(str(alb_name), case=False)].head(n=limit)

    single_album_barchart = px.bar(df_filtered, y='Song', x='Stream Count',
                                   title=f'Titel vom Album "{alb_name}"', height=1000,
                                   # text_auto='.2s',
                                   orientation='h',
                                   color='Stream Count', color_continuous_scale=default_color_scale,
                                   template=template_from_url(theme),
                                   custom_data=['Album', 'Artist', 'Song', 'Stream Count'])
    single_album_barchart.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
    single_album_barchart.update_layout(yaxis=dict(autorange="reversed"))

    single_album_barchart.update_layout(
        # plot_bgcolor=colors['background'],
        # paper_bgcolor=colors['background'],
        # font_color=colors['amaranth'],
        transition_duration=500
    )

    single_album_barchart.update_traces(
        hovertemplate="<br>".join([
            "Album: %{customdata[0]}",
            "Artist: %{customdata[1]}",
            "Song: %{customdata[2]}",
            "Streams: %{customdata[3]}"
        ])
    )

    return single_album_barchart
