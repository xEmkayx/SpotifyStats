import dash
import plotly.express as px
from dash import html, dcc, callback, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

from analysis.graphics.webapp.helpers.consts import *
from analysis.graphics.webapp.helpers.df_filenames import *
from analysis.graphics.webapp.select_statements import *
from analysis.graphics.webapp.df_files import dataframe_loader

dash.register_page(__name__)

# df = pd.read_csv(fr'{df_common_path}\{fn_df_anz_streams}.csv')

# df = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')
df = dataframe_loader.get_default_dataframe()

gr = df.groupby('Gespielt am').agg({'Song-ID':'first', 'Song':'first', 'Artist':', '.join, 'Artist-ID':', '.join,
                                    'Album':'first', 'Album-ID':'first'})

counted = gr.value_counts('Song-ID').rename({1:'Song-ID', 2:'Anzahl Streams'}).sort_index().reset_index()
counted.set_axis(['Song-ID', 'Anzahl Streams'], axis=1, inplace=True)

rest = gr.reset_index().drop('Gespielt am', axis=1).drop_duplicates('Song-ID').sort_values('Song-ID')

df_combined = pd.merge(counted, rest).sort_values('Anzahl Streams', ascending=False)

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
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value"),
)
def update_graph_theme(theme):
    song_streams_plot = px.sunburst(df_combined.head(n=1000),
                                    path=['Artist', 'Album', 'Song'], values='Anzahl Streams',
                                    title='Anzahl aller Song Streams',
                                    color='Anzahl Streams', color_continuous_scale=default_color_scale,
                                    template=template_from_url(theme),
                                    height=1000,
                                    custom_data=['Song', 'Anzahl Streams', 'Song-ID', 'Artist', 'Artist-ID',
                                                 'Album', 'Album-ID'])

    # song_streams_plot.update_layout(
    #     plot_bgcolor=colors['background'],
    #     paper_bgcolor=colors['background'],
    #     font_color=colors['amaranth']
    # )

    song_streams_plot.update_traces(
        hovertemplate="<br>".join([
            "Song: %{customdata[0]}",
            "Anzahl Streams: %{customdata[1]}",
            "Song-ID: %{customdata[2]}",
            "Artist: %{customdata[3]}",
            "Artist-ID(s): %{customdata[4]}",
            "Album: %{customdata[5]}",
            "Album-ID: %{customdata[6]}",
        ])
    )

    return song_streams_plot
