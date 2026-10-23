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
    html.P("Analyse deiner Spotify-Historie: Top-Charts, Dashboard, Hörhistorie und Detailansichten."),
    dbc.Button("Zu Top Songs", href="/top-songs", color="primary", className="me-2"),
    dbc.Button("Zum Dashboard", href="/dashboard", color="secondary", outline=True)
    ])
    ]), md=6),
    dbc.Col(dbc.Card([
    dbc.CardBody([
    html.H5("Tipps", className="card-title"),
    html.Ul([
    html.Li("Filter und Aggregationen laufen serverseitig – schnell bei großen Daten."),
    html.Li("Neue Streams werden automatisch erkannt; Refresh erzwingt ein Neuladen."),
    html.Li("Design via Bootswatch-Theme – leicht austauschbar."),
    ])
    ])
    ]), md=6),
    ])
    ], fluid=True)