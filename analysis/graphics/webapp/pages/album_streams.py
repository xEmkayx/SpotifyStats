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

# gr = df.groupby(['Album-ID', 'Album'], as_index=False).size()  # .to_frame()
# df_sorted = gr.sort_values(by=['size'], ascending=False)

# df = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')
df = dataframe_loader.get_default_dataframe()

gr = df.groupby('Played at').agg({'Album': 'first', 'Album-ID': 'first',
                                    'Artist': ', '.join, 'Artist-ID': ', '.join,
                                    })
counted = gr.value_counts('Album-ID').rename({1: 'Album-ID', 2: 'Stream Count'}).sort_index().reset_index()
counted.set_axis(['Album-ID', 'Stream Count'], axis=1, inplace=True)
rest = gr.reset_index().drop('Played at', axis=1).drop_duplicates('Album-ID').sort_values('Album-ID')
df_combined = pd.merge(counted, rest).sort_values('Stream Count', ascending=False)

graph = dcc.Graph(
    id='album-streams-line'
)

layout = html.Div(children=[
    html.H1(children='Album Streams'),
    graph
])


@callback(
    Output('album-streams-line', 'figure'),
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value"),
)
def update_graph_theme(theme):
    all_albums_plot = px.bar(df_combined.head(n=50), x='Album', y="Stream Count", height=1000,  # markers=True,
                             title='Top Albums Streams',
                             color='Stream Count', color_continuous_scale=default_color_scale,
                             custom_data=['Album', 'Stream Count', 'Artist', 'Album-ID', 'Artist-ID'],
                             template=template_from_url(theme)
                             )

    all_albums_plot.update_traces(
        hovertemplate="<br>".join([
            "Album: %{customdata[0]}",
            "Stream Count: %{customdata[1]}",
            "Artist: %{customdata[2]}",
            "Album-ID: %{customdata[3]}",
            "Artist-ID: %{customdata[4]}",
        ])
    )

    # all_albums_plot.update_layout(
    #     plot_bgcolor=colors['background'],
    #     paper_bgcolor=colors['background'],
    #     font_color=colors['amaranth']
    # )

    all_albums_plot.update_xaxes(showgrid=True, gridwidth=1,  # gridcolor='LightPink'
                                 )
    all_albums_plot.update_yaxes(showgrid=True, gridwidth=1,  # gridcolor='LightPink'
                                 )

    return all_albums_plot
