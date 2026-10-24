import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/", name="Home", order=0)

def layout():
    return dbc.Container([
    dbc.Row([
    dbc.Col(dbc.Card([
    dbc.CardBody([
    html.H4("Willkommen!", className="card-title"),
    html.P("Alles über deine Spotify-Historie: deine Top-Songs, wann du was hörst und wie sich deine Playlists verändern."),
    dbc.Button("Zu Top Songs", href="/top-songs", color="primary", className="me-2"),
    dbc.Button("Zum Dashboard", href="/dashboard", color="secondary", outline=True)
    ])
    ]), md=6),
    dbc.Col(dbc.Card([
    dbc.CardBody([
    html.H5("Tipps", className="card-title"),
    html.Ul([
    html.Li("Neue Streams tauchen nach spätestens einer Minute auf."),
    html.Li("Songs, die es in mehreren Versionen gibt, werden zusammengezählt – unter Bibliothek → Versionen "
            "siehst du, welche."),
    html.Li("Unter Bibliothek → Playlists findest du den Verlauf deiner Playlists und kannst alte Stände "
            "wiederherstellen."),
    ])
    ])
    ]), md=6),
    ])
    ], fluid=True)