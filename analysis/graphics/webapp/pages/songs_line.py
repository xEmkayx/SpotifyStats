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

gr = df.groupby(['Song-ID', 'Song', 'Künstler', 'Künstler-ID', 'Album', 'Album-ID'], as_index=False).size()  # .to_frame()
df_sorted = gr.sort_values(by=['size'], ascending=False)

theme_change = ThemeChangerAIO(aio_id="theme")

graph = dcc.Graph(
    id='all-songs-line',
)

layout = html.Div(children=[
    html.H1(children='All Song Streams'),
    dcc.Loading(
        id='load-songs-line',
        children=[graph],
    ),
    # theme_change
])


@callback(
    Output("all-songs-line", "figure"),
    Input(ThemeChangerAIO.ids.radio("theme"), "value"),
)
def update_graph_theme(theme):
    fig = px.line(df_sorted.head(n=100), x="Song", y="size", template=template_from_url(theme),
                  markers=True, height=1000,
                  title=f'Streamzahlen aller Künstler"',
                  custom_data=['Song', 'size', 'Song-ID', 'Künstler', 'Künstler-ID', 'Album', 'Album-ID'])

    fig.update_traces(
        hovertemplate="<br>".join([
            # "ColX: %{x}",
            # "ColY: %{y}",
            "Song: %{customdata[0]}",
            "Anzahl Streams: %{customdata[1]}",
            "Song-ID: %{customdata[2]}",
            "Künstler: %{customdata[3]}",
            "Künstler-ID: %{customdata[4]}",
            "Album: %{customdata[5]}",
            "Album-ID: %{customdata[6]}",
        ])
    )
    return fig
