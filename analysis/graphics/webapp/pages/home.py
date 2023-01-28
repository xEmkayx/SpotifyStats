import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(__name__)

# df = pd.read_csv(fr'{df_common_path}\{fn_df_anz_top_album_streams}.csv')
# sunb_top_albums_plot = px.sunburst(df.head(n=1000), path=['Album', 'Song'], values='Anzahl Streams',
#                                    title='Anzahl der Album-Streams nach Alben',
#                                    color='Anzahl Streams', color_continuous_scale='tealrose', template='seaborn')
#
# sunb_top_albums_plot.update_layout(
#     plot_bgcolor=colors['background'],
#     paper_bgcolor=colors['background'],
#     font_color=colors['amaranth']
# )
# sunb_top_albums_plot.update_traces(line_color=(colors['amaranth'])) # , line_width=5

# sunb_top_albums_plot.update_xaxes(showgrid=False)
# sunb_top_albums_plot.update_yaxes(showgrid=False)

card = dbc.Card(
    [
        dbc.CardImg(src="../assets/images/album_streams.png", top=True),
        dbc.CardBody(
            [
                html.H4("Card title", className="card-title"),
                html.P(
                    "Some quick example text to build on the card title and "
                    "make up the bulk of the card's content.",
                    className="card-text",
                ),
                dbc.Button("Go somewhere", color="primary"),
            ]
        ),
    ],
    style={"width": "18rem"},
)
card2 = dbc.Card(
    [
        dbc.CardImg(src="../assets/images/album_streams.png", top=True),
        dbc.CardBody(
            [
                html.H4("Card 2 title", className="card-title"),
                html.P(
                    "Some quick example text to build on the card title and "
                    "make up the bulk of the card's content.",
                    className="card-text",
                ),
                dbc.Button("Go somewhere", color="primary"),
            ]
        ),
    ],
    style={"width": "18rem"},
)
cards = [card, card2]



layout = dbc.Container(cards, fluid=True)

# layout = html.Div(children=[
#     html.H1(children='Homescreen'),
#     html.Div(children=[
#
#     ])
# ])
