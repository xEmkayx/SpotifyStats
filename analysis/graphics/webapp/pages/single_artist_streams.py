import dash
from dash import html, dcc, callback, Input, Output
from analysis.graphics.webapp.select_statements import *
from analysis.graphics.webapp.helpers.colors import colors
from analysis.graphics.webapp.helpers.df_filenames import *
from analysis.graphics.webapp.helpers.consts import *
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url
import plotly.express as px

dash.register_page(__name__)

# df = pd.read_csv(fr'{df_common_path}\{fn_df_anz_streams}.csv')
df = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')

gr = df.groupby('Gespielt am').agg({'Song-ID':'first', 'Song':'first', 'Künstler':', '.join, 'Künstler-ID':', '.join,
                                    'Album':'first', 'Album-ID':'first'})

counted = gr.value_counts('Song-ID').rename({1:'Song-ID', 2:'Anzahl Streams'}).sort_index().reset_index()
counted.set_axis(['Song-ID', 'Anzahl Streams'], axis=1, inplace=True)

rest = gr.reset_index().drop('Gespielt am', axis=1).drop_duplicates('Song-ID').sort_values('Song-ID')

df_combined = pd.merge(counted, rest).sort_values('Anzahl Streams', ascending=False)

rbSelectionMethod = dcc.RadioItems(
    id='radio-items-sart',
    options=[
        {'label': 'Artist Name', 'value': 1},
        {'label': 'Artist ID', 'value': 2}
    ],
    value='Artist Name',
    labelStyle={'display': 'block'}
)

graph = dcc.Graph(
    id='single-artists-line'
)

layout = html.Div(children=[
    html.H1(children='Single Artist Streams'),
    html.Div(children=[
            html.Div(
                children=[
                    rbSelectionMethod,
                ]
            ),
            html.Div(children=[
                dcc.Input(type='text', id='inp-artist-name'),
            ]),
            html.Div(children=[
                dcc.Input(type='number', id='inp-limit', value=20),
            ]),
        ], style={
            'padding': '20px',
        }
             ),
    html.Br(),
    dcc.Loading(
        id='load-single-artists',
        children=[graph],
    ),
])


@callback(
    Output('single-artists-line', 'figure'),
    Input('inp-artist-name', 'value'),
    Input('inp-limit', 'value'),
    Input('radio-items-sart', 'value'),
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value"),
)
def update_graph(art_name, limit, rbvalue, theme):
    art_name = str(art_name)
    # TODO: REGEX BUTTON
    if rbvalue == 1:
        df_filtered = df_combined[df_combined['Künstler'].str.contains(str(art_name), case=False)].head(n=limit)
    elif rbvalue == 2:
        df_filtered = df_combined[df_combined['Künstler-ID'].str.contains(str(art_name), case=False)].head(n=limit)
    else:
        df_filtered = df_combined[df_combined['Künstler'].str.contains(str(art_name), case=False)].head(n=limit)

    single_artist_barchart = px.bar(df_filtered, y='Song', x='Anzahl Streams',
                                    title=f'Songs von "{art_name}"', height=1000,
                                    text_auto='.2s', orientation='h',
                                    color='Anzahl Streams', color_continuous_scale=default_color_scale,
                                    template=template_from_url(theme),
                                    custom_data=['Künstler', 'Song', 'Anzahl Streams'])
    single_artist_barchart.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
    single_artist_barchart.update_layout(yaxis=dict(autorange="reversed"))

    single_artist_barchart.update_layout(
        # plot_bgcolor=colors['background'],
        # paper_bgcolor=colors['background'],
        # font_color=colors['amaranth'],
        transition_duration=500
    )

    single_artist_barchart.update_traces(
        hovertemplate="<br>".join([
            "Künstler: %{customdata[0]}",
            "Song: %{customdata[1]}",
            "Streams: %{customdata[2]}"
        ])
    )

    # return single_artists_plot
    return single_artist_barchart
