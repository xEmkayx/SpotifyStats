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

gr = df.groupby('Gespielt am').agg(
    {'Song-ID': 'first', 'Song': 'first', 'Künstler': ', '.join, 'Künstler-ID': ', '.join,
     'Album': 'first', 'Album-ID': 'first'})

counted = gr.value_counts('Song-ID').rename({1: 'Song-ID', 2: 'Anzahl Streams'}).sort_index().reset_index()
counted.set_axis(['Song-ID', 'Anzahl Streams'], axis=1, inplace=True)

rest = gr.reset_index().drop('Gespielt am', axis=1).drop_duplicates('Song-ID').sort_values('Song-ID')

df_combined = pd.merge(counted, rest).sort_values('Anzahl Streams', ascending=False)

graph = dcc.Graph(
    id='albums-sunburst'
)

layout = html.Div(children=[
    html.H1(children='Album Streams'),
    dcc.Loading(
        id='load-sb-album', children=[graph]
    )
])


@callback(
    Output('albums-sunburst', 'figure'),
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value")
)
def update_graph_theme(theme):
    fig = px.sunburst(df_combined.head(n=1000), path=['Album', 'Song'], values='Anzahl Streams',
                      title='Anzahl der Album-Streams nach Alben',
                      color='Anzahl Streams', color_continuous_scale=default_color_scale, template=template_from_url(theme),
                      height=1000
                      )
    return fig
