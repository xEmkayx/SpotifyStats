import os
from urllib.parse import urlparse, parse_qs

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback, no_update, ctx

from auth.spotify_auth_manager import SpotifyServerAuth

from frontend_new.config import CACHE_TIMEOUT_SEC, DATA_VERSION_TTL_SEC
from frontend_new.core.data_version import bump_data_version
from frontend_new.core.extensions import cache
from frontend_new.services.dashboard import db_status
from common import settings
from frontend_new.services.playlists import local_time
from frontend_new.services.spotify_images import library_write_allowed

dash.register_page(__name__, path="/settings", name="Einstellungen", order=90)


def layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Deine Daten"),
                dbc.CardBody(html.Div(id="settings-status", children=_status_list()))
            ]), md=6),
            dbc.Col(dbc.Card([
                dbc.CardHeader("Aktualisierung"),
                dbc.CardBody([
                    html.P([
                        f"Neue Streams tauchen automatisch auf, spätestens nach {DATA_VERSION_TTL_SEC} Sekunden. "
                        f"Falls etwas nicht stimmt, kannst du hier alles neu laden."
                    ], className="text-muted"),
                    dbc.Button([html.I(className="bi bi-arrow-clockwise me-1"), "Alles neu laden"],
                               id="settings-clear-cache", color="primary"),
                    html.Div(id="settings-feedback", className="toast-area"),
                ])
            ]), md=6),
        ], className="mb-3"),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Veraltete Versionen in Playlists"),
                dbc.CardBody(_auto_replace_controls()),
            ]), md=6, className="mb-3"),
            dbc.Col(dbc.Card([
                dbc.CardHeader("Spotify-Verbindung"),
                dbc.CardBody(_spotify_connection()),
            ]), md=6, className="mb-3"),
        ]),
    ], fluid=True)


def _connection_status():
    try:
        scopes = SpotifyServerAuth().granted_scopes()
    except Exception:
        scopes = set()
    if not scopes:
        return dbc.Alert("Nicht mit Spotify verbunden.", color="warning", className="py-2 mb-2")
    lines = [html.Div([html.I(className="bi bi-check-circle me-1"), "Mit Spotify verbunden"])]
    if "user-library-modify" in scopes:
        lines.append(html.Div([html.I(className="bi bi-check-circle me-1"), "Darf Lieblingssongs ändern"]))
    else:
        lines.append(html.Div([html.I(className="bi bi-x-circle me-1"),
                               "Darf Lieblingssongs noch nicht ändern – dafür einmal neu verbinden"]))
    return html.Div(lines, className="small mb-2")


def _spotify_connection():
    return [
        html.Div(id="settings-spotify-status", children=_connection_status()),
        dcc.Store(id="settings-auth-state"),
        dbc.Button([html.I(className="bi bi-spotify me-1"), "Mit Spotify neu verbinden"],
                   id="settings-auth-start", color="success", outline=True, size="sm"),
        dbc.Collapse(id="settings-auth-steps", is_open=False, children=html.Div([
            html.Ol([
                html.Li(["Öffne den Link und melde dich bei Spotify an: ",
                         html.A("Bei Spotify anmelden", id="settings-auth-link", href="#", target="_blank")]),
                html.Li("Danach leitet Spotify dich auf eine Seite weiter, die nicht lädt – das ist normal."),
                html.Li("Kopier die komplette Adresse aus der Adresszeile und füg sie hier ein:"),
            ], className="small ps-3 mb-2"),
            dbc.InputGroup([
                dbc.Input(id="settings-auth-url", placeholder="http://127.0.0.1:8080/?code=…"),
                dbc.Button("Verbindung speichern", id="settings-auth-complete", color="primary"),
            ], size="sm"),
        ], className="mt-3")),
    ]


def _auto_replace_controls():
    liked_ok = library_write_allowed()
    return [
        html.P("Spotify ersetzt manche Songs durch eine neuere Version und spielt dann nur noch die neue ab. "
               "Wenn du willst, werden solche Songs bei jedem stündlichen Abgleich automatisch ausgetauscht. "
               "Jeder Song bleibt dabei an seiner Stelle, und vorher wird der Stand der Playlist gespeichert – "
               "im Verlauf siehst du also genau, was getauscht wurde.", className="text-muted small"),
        dbc.Switch(id="settings-auto-playlists", label="In meinen Playlists automatisch austauschen",
                   value=settings.get_flag(settings.AUTO_REPLACE_PLAYLISTS), className="mb-2"),
        dbc.Switch(id="settings-auto-liked", label="Auch bei meinen Lieblingssongs (landen dabei ganz oben)",
                   value=settings.get_flag(settings.AUTO_REPLACE_LIKED) and liked_ok, disabled=not liked_ok),
        html.Small("Für die Lieblingssongs fehlt noch eine Berechtigung bei Spotify („user-library-modify“). "
                   "Dafür musst du die Verbindung zu Spotify einmal neu herstellen.",
                   className="text-muted d-block mt-1") if not liked_ok else None,
        html.Small(["Einzelne Playlists kannst du auch selbst austauschen, unter ",
                    html.A("Bibliothek → Playlists", href="/playlists"), "."], className="text-muted d-block mt-2"),
    ]


def _status_list():
    try:
        s = db_status()
    except Exception as e:
        return dbc.Alert(f"Die Datenbank ist gerade nicht erreichbar: {e}", color="danger")
    rows = [
        ("Streams", f"{s['streams']:,}".replace(",", ".")),
        ("Erster Stream", local_time(s["first_stream"])),
        ("Letzter Stream", local_time(s["last_stream"])),
        ("Songs", f"{s['songs']:,}".replace(",", ".")),
        ("Artists", f"{s['artists']:,}".replace(",", ".")),
        ("Alben", f"{s['albums']:,}".replace(",", ".")),
    ]
    return dbc.ListGroup([
        dbc.ListGroupItem([html.Span(k), html.Span(v, className="ms-auto text-muted")],
                          className="d-flex justify-content-between")
        for k, v in rows
    ], flush=True)


@callback(
    Output("settings-feedback", "children"),
    Output("settings-status", "children"),
    Output("cache-version", "data", allow_duplicate=True),
    Input("settings-clear-cache", "n_clicks"),
    prevent_initial_call=True
)
def clear_cache(n):
    if not n:
        return no_update, no_update, no_update
    cache.clear()
    version = bump_data_version()
    return dbc.Alert("Erledigt – alles wird neu geladen.", color="success", duration=4000), \
        _status_list(), version


@callback(
    Output("settings-feedback", "children", allow_duplicate=True),
    Input("settings-auto-playlists", "value"),
    Input("settings-auto-liked", "value"),
    prevent_initial_call=True
)
def save_auto_replace(playlists_on, liked_on):
    if ctx.triggered_id == "settings-auto-playlists":
        settings.set_flag(settings.AUTO_REPLACE_PLAYLISTS, bool(playlists_on))
        text = ("Ab jetzt werden veraltete Versionen in deinen Playlists automatisch ausgetauscht."
                if playlists_on else "Automatisches Austauschen in Playlists ist aus.")
    else:
        settings.set_flag(settings.AUTO_REPLACE_LIKED, bool(liked_on))
        text = ("Ab jetzt auch bei deinen Lieblingssongs." if liked_on
                else "Lieblingssongs werden nicht mehr automatisch ausgetauscht.")
    return dbc.Alert(text, color="success", duration=3500)


@callback(
    Output("settings-auth-steps", "is_open"),
    Output("settings-auth-link", "href"),
    Output("settings-auth-state", "data"),
    Input("settings-auth-start", "n_clicks"),
    prevent_initial_call=True
)
def start_auth(_n):
    state = os.urandom(16).hex()
    return True, SpotifyServerAuth().get_authorize_url(state=state), state


@callback(
    Output("settings-feedback", "children", allow_duplicate=True),
    Output("settings-spotify-status", "children"),
    Output("settings-auth-steps", "is_open", allow_duplicate=True),
    Input("settings-auth-complete", "n_clicks"),
    State("settings-auth-url", "value"),
    State("settings-auth-state", "data"),
    prevent_initial_call=True
)
def complete_auth(_n, pasted, expected_state):
    pasted = (pasted or "").strip()
    # Komplette Adresse (http…?code=…&state=…) oder nur der Code
    query = parse_qs(urlparse(pasted).query) if pasted.startswith("http") else {"code": [pasted]}
    code = (query.get("code") or [""])[0]
    if query.get("error"):
        return dbc.Alert("Spotify hat die Anmeldung abgelehnt.", color="warning", duration=5000), no_update, no_update
    if not code:
        return dbc.Alert("Da fehlt der Code – bitte die komplette Adresse einfügen.", color="warning",
                         duration=5000), no_update, no_update
    if query.get("state") and query["state"][0] != expected_state:
        return dbc.Alert("Die Adresse gehört zu einer älteren Anmeldung. Bitte den Link oben noch einmal öffnen.",
                         color="warning", duration=6000), no_update, no_update
    try:
        SpotifyServerAuth().complete_authorization(code)
    except Exception as e:
        return dbc.Alert(f"Das hat nicht geklappt: {e}", color="danger", dismissable=True), no_update, no_update
    return dbc.Alert("Verbunden! Deine Lieblingssongs können jetzt auch ausgetauscht werden.", color="success",
                     duration=5000), _connection_status(), False
