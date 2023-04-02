import dash
import plotly.express as px
from dash import html, dcc, callback, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

from analysis.graphics.webapp.helpers.df_filenames import *
from analysis.graphics.webapp.select_statements import *
from analysis.graphics.webapp.df_files import dataframe_loader

dash.register_page(__name__)

# df = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')
df = dataframe_loader.get_default_dataframe()

gr = df.groupby(['Artist', 'Artist-ID'], as_index=False).size()
df_sorted = gr.sort_values(by=['size'], ascending=False)
df_sorted.rename({1:'Artist', 2:'Artist-ID', 3:'Anzahl Streams'})
df_sorted.set_axis(['Artist', 'Artist-ID', 'Anzahl Streams'], axis=1, inplace=True)

theme_change = ThemeChangerAIO(aio_id="theme")

graph = dcc.Graph(
    id='all-artists-line',
    # figure=all_artists_plot
)

layout = html.Div(children=[
    html.H1(children='All Artist Streams'),
    dcc.Loading(
        id='load-top-artists',
        children=[graph],
    ),
    # theme_change
])


@callback(
    Output("all-artists-line", "figure"),
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value"),
)
def update_graph_theme(theme):
    fig = px.line(df_sorted.head(n=500), x="Artist", y="Anzahl Streams", template=template_from_url(theme),
                  markers=True, height=1000,
                  title=f'Streamzahlen aller Artist"',
                  custom_data=['Artist', 'Anzahl Streams', 'Artist-ID'])

    fig.update_traces(
        hovertemplate="<br>".join([
            "Artist: %{customdata[0]}",
            "Anzahl Streams: %{customdata[1]}",
            "Artist-ID: %{customdata[2]}",
        ])
    )
    return fig
