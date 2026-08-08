import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/", name="Home")

def layout():
    return dbc.Container([
    dbc.Row([
    dbc.Col(dbc.Card([
    dbc.CardBody([
    html.H4("Willkommen!", className="card-title"),
    html.P("Analyse deiner Spotify-Historie. Starte mit den Top Songs oder füge später weitere Seiten hinzu."),
    dbc.Button("Zu Top Songs", href="/top-songs", color="primary")
    ])
    ]), md=6),
    dbc.Col(dbc.Card([
    dbc.CardBody([
    html.H5("Tipps", className="card-title"),
    html.Ul([
    html.Li("Filter und Aggregationen laufen serverseitig – schnell bei großen Daten."),
    html.Li("Refresh lädt die Cache-Version neu (zur Laufzeit)."),
    html.Li("Design via Bootswatch-Theme – leicht austauschbar."),
    ])
    ])
    ]), md=6),
    ])
    ], fluid=True)