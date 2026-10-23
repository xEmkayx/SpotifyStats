import dash
import dash_bootstrap_components as dbc
from dash import html, Input, Output, callback, no_update

from frontend_new.config import CACHE_TIMEOUT_SEC, DATA_VERSION_TTL_SEC
from frontend_new.core.data_version import bump_data_version
from frontend_new.core.extensions import cache
from frontend_new.services.dashboard import db_status

dash.register_page(__name__, path="/settings", name="Einstellungen", order=90)


def layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Datenbestand"),
                dbc.CardBody(html.Div(id="settings-status", children=_status_list()))
            ]), md=6),
            dbc.Col(dbc.Card([
                dbc.CardHeader("Aktualisierung"),
                dbc.CardBody([
                    html.P([
                        f"Neue Streams werden automatisch erkannt (Prüfung alle {DATA_VERSION_TTL_SEC} s). "
                        f"Berechnete Ansichten werden bis zu {CACHE_TIMEOUT_SEC // 60} Minuten zwischengespeichert."
                    ], className="text-muted"),
                    dbc.Button([html.I(className="bi bi-trash me-1"), "Cache leeren & Daten neu laden"],
                               id="settings-clear-cache", color="primary"),
                    html.Div(id="settings-feedback", className="mt-3"),
                ])
            ]), md=6),
        ])
    ], fluid=True)


def _status_list():
    try:
        s = db_status()
    except Exception as e:
        return dbc.Alert(f"Datenbank nicht erreichbar: {e}", color="danger")
    rows = [
        ("Streams", f"{s['streams']:,}".replace(",", ".")),
        ("Erster Stream", str(s["first_stream"] or "—")[:19]),
        ("Letzter Stream", str(s["last_stream"] or "—")[:19]),
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
    return dbc.Alert("Cache geleert, Daten werden neu geladen.", color="success", duration=4000), \
        _status_list(), version
