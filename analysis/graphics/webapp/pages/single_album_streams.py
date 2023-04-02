import dash
import plotly.express as px
from dash import html, dcc, callback, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

from analysis.graphics.webapp.helpers.consts import *
from analysis.graphics.webapp.helpers.df_filenames import *
from analysis.graphics.webapp.select_statements import *
from analysis.graphics.webapp.df_files import dataframe_loader

dash.register_page(__name__)

# df = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')
df = dataframe_loader.get_default_dataframe()

gr = df.groupby('Gespielt am').agg(
    {'Song-ID': 'first', 'Song': 'first', 'Künstler': ', '.join, 'Künstler-ID': ', '.join,
     'Album': 'first', 'Album-ID': 'first'})

counted = gr.value_counts('Song-ID').rename({1: 'Song-ID', 2: 'Anzahl Streams'}).sort_index().reset_index()
counted.set_axis(['Song-ID', 'Anzahl Streams'], axis=1, inplace=True)

rest = gr.reset_index().drop('Gespielt am', axis=1).drop_duplicates('Song-ID').sort_values('Song-ID')

df_combined = pd.merge(counted, rest).sort_values('Anzahl Streams', ascending=False)

graph = dcc.Graph(
    id='single-albums-bar'
)

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

layout = html.Div(children=[
    html.H1(children='Single Album Streams'),
    html.Div(className='container-single',
             children=[
                 html.Div(
                     className='container-radiobuttons',
                     children=[
                         rbSelectionMethod,
                     ]
                 ),
                 html.Div(children=[
                     dcc.Input(type='text', id='inp-album-name'),
                 ]),
                 html.Div(children=[
                     dcc.Input(type='number', id='inp-limit', value=20),
                 ]),
             ],
             ),
    # dcc.Input(type='text', id='inp-album-name'),
    # dcc.Input(type='number', id='inp-limit', value=20),
    html.Br(),
    dcc.Loading(
        id='load-single-album',
        children=[graph],
    ),
])


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

    single_album_barchart = px.bar(df_filtered, y='Song', x='Anzahl Streams',
                                   title=f'Titel vom Album "{alb_name}"', height=1000,
                                   # text_auto='.2s',
                                   orientation='h',
                                   color='Anzahl Streams', color_continuous_scale=default_color_scale,
                                   template=template_from_url(theme),
                                   custom_data=['Album', 'Künstler', 'Song', 'Anzahl Streams'])
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
            "Künstler: %{customdata[1]}",
            "Song: %{customdata[2]}",
            "Streams: %{customdata[3]}"
        ])
    )

    return single_album_barchart
