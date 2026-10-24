import dash
import dash_bootstrap_components as dbc
from dash import html, Input, Output, callback, no_update, ctx

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
            ]), md=6),
        ]),
    ], fluid=True)


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
