import dash
from dash import html, dcc, callback, Input, Output
from analysis.graphics.webapp.select_statements import *
from analysis.graphics.webapp.helpers.colors import colors
from analysis.graphics.webapp.helpers.df_filenames import *
from analysis.graphics.webapp.helpers.consts import *
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url
import dash_bootstrap_components as dbc
import plotly.express as px

dash.register_page(__name__)

df = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')

gr = df.groupby('Gespielt am').agg(
    {'Song-ID': 'first', 'Song': 'first', 'Künstler': ', '.join, 'Künstler-ID': ', '.join,
     'Album': 'first', 'Album-ID': 'first'})

counted = gr.value_counts('Song-ID').rename({1: 'Song-ID', 2: 'Anzahl Streams'}).sort_index().reset_index()
counted.set_axis(['Song-ID', 'Anzahl Streams'], axis=1, inplace=True)

rest = gr.reset_index().drop('Gespielt am', axis=1).drop_duplicates('Song-ID').sort_values('Song-ID')

df_combined = pd.merge(counted, rest).sort_values('Anzahl Streams', ascending=False)

graph = dcc.Graph(
    id='song-count-line',
)

table = dbc.Table.from_dataframe(df_combined.head(n=1000), striped=True, bordered=True, hover=True)

tab_normal = dcc.Tab(
    children=[
        html.Div([
            html.H1(children='All Song Streams'),
            dcc.Loading(
                id='load-song-count',
                children=[graph],
            ),
        ], ),
    ],
    label='Graph',
    selected_className='custom-tab--selected',
)

tab_table = dcc.Tab(
    html.Div(
        [
            dcc.Loading(
                table
            )
        ]
    ),
    label='Tabelle',
    selected_className='custom-tab--selected'
)

tabs = dcc.Tabs(
    [
        tab_normal,
        tab_table
    ],
    parent_className='custom-tabs',
    className='custom-tabs-container',
)

layout = html.Div(children=[
    tabs
    # html.H1(children='All Song Streams'),
    # dcc.Loading(
    #     id='load-song-count',
    #     children=[graph],
    # ),
])


@callback(
    Output("song-count-line", "figure"),
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value"),
)
def update_graph_theme(theme):
    fig = px.line(df_combined.head(n=100), x="Song", y="Anzahl Streams", template=template_from_url(theme),
                  markers=True, height=1000,
                  title=f'Streamzahlen aller Songs',
                  custom_data=['Song', 'Anzahl Streams', 'Song-ID', 'Künstler', 'Künstler-ID', 'Album', 'Album-ID'])

    fig.update_traces(
        hovertemplate="<br>".join([
            "Song: %{customdata[0]}",
            "Anzahl Streams: %{customdata[1]}",
            "Song-ID: %{customdata[2]}",
            "Künstler: %{customdata[3]}",
            "Künstler-ID(s): %{customdata[4]}",
            "Album: %{customdata[5]}",
            "Album-ID: %{customdata[6]}",
        ])
    )
    return fig
