import dash
from dash import html, dcc, callback, Input, Output
from analysis.graphics.webapp.select_statements import *
from analysis.graphics.webapp.helpers.colors import colors
from analysis.graphics.webapp.helpers.df_filenames import *
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url
import plotly.express as px

dash.register_page(__name__)

df = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')

gr = df.groupby(['Künstler', 'Künstler-ID'], as_index=False).size()
df_sorted = gr.sort_values(by=['size'], ascending=False)
df_sorted.rename({1:'Künstler', 2:'Künstler-ID', 3:'Anzahl Streams'})
df_sorted.set_axis(['Künstler', 'Künstler-ID', 'Anzahl Streams'], axis=1, inplace=True)

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
    fig = px.line(df_sorted.head(n=500), x="Künstler", y="Anzahl Streams", template=template_from_url(theme),
                  markers=True, height=1000,
                  title=f'Streamzahlen aller Künstler"',
                  custom_data=['Künstler', 'Anzahl Streams', 'Künstler-ID'])

    fig.update_traces(
        hovertemplate="<br>".join([
            "Künstler: %{customdata[0]}",
            "Anzahl Streams: %{customdata[1]}",
            "Künstler-ID: %{customdata[2]}",
        ])
    )
    return fig
