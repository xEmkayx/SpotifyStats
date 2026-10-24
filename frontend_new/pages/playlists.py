from urllib.parse import parse_qs

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback, ctx, ALL, no_update, dash_table

from common.playlists import actions, history
from frontend_new.components.empty_state import empty_state
from frontend_new.core.data_version import bump_data_version
from frontend_new.services.playlists import (
    playlist_overview, playlist_info, snapshots, snapshot_diff, diff_summary, local_time
)
from frontend_new.services.spotify_images import spotify_client

dash.register_page(__name__, path="/playlists", name="Playlists", group="Bibliothek", order=30)

OP_STYLE = {
    "added": ("+", "success", "hinzugefügt"),
    "removed": ("−", "danger", "entfernt"),
    "moved": ("↕", "info", "verschoben"),
    "replaced": ("⇄", "warning", "Version ersetzt"),
}
REASON_LABELS = {"initial": "erster Stand", "sync": "Änderung", "manual": "manuell geladen",
                 "before_restore": "vor Zurücksetzen", "restore": "zurückgesetzt",
                 "before_replace": "vor Ersetzen", "replace": "Versionen ersetzt"}
DIFF_LIMIT = 300


def _playlist_id_from_search(search: str):
    return (parse_qs((search or "").lstrip("?")).get("id") or [None])[0]


# --- Übersicht ---

def _overview_layout():
    return html.Div([
        dbc.Row([
            dbc.Col(dbc.Input(id="pl-search", placeholder="Playlist suchen", debounce=True), md=5),
            dbc.Col(dbc.Select(id="pl-sort", value="changed", options=[
                {"label": "Sortieren: zuletzt geändert", "value": "changed"},
                {"label": "Sortieren: Name", "value": "name"},
                {"label": "Sortieren: Anzahl Titel", "value": "tracks"},
                {"label": "Sortieren: ersetzte Versionen", "value": "superseded"}]), md=4),
            dbc.Col(dbc.Checkbox(id="pl-deleted", label="Gelöschte anzeigen", value=False), md=3,
                    className="d-flex align-items-center"),
        ], className="g-2 mb-3"),
        html.Small("Nur eigene Playlists (von Spotify generierte und fremde werden nicht verfolgt). "
                   "Der Abgleich läuft stündlich im Backend.", className="text-muted d-block mb-2"),
        dcc.Loading(html.Div(id="pl-list")),
    ])


def _playlist_row(p: dict):
    badges = []
    if p["deleted_at"]:
        badges.append(dbc.Badge("gelöscht", color="danger", className="me-1"))
    if p["superseded"]:
        badges.append(dbc.Badge(f"{p['superseded']} ersetzte Versionen", color="warning", className="me-1"))
    img = html.Img(src=p["image_url"], style={"width": "48px", "height": "48px", "objectFit": "cover",
                                             "borderRadius": "6px"}) if p["image_url"] else \
        html.Div(html.I(className="bi bi-music-note-list"), className="text-muted",
                 style={"width": "48px", "height": "48px", "display": "flex", "alignItems": "center",
                        "justifyContent": "center", "fontSize": "22px"})
    return dbc.ListGroupItem(html.Div([
        img,
        html.Div([
            html.Div([html.Span(p["name"] or p["playlist_id"], className="fw-semibold me-2"), *badges]),
            html.Small(f"{p['track_count'] or 0} Titel · {p['snapshots']} Stände · zuletzt geändert "
                       f"{local_time(p['last_changed_at'] or p['first_seen_at'])}", className="text-muted"),
        ], className="ms-3 flex-grow-1"),
        html.I(className="bi bi-chevron-right text-muted"),
    ], className="d-flex align-items-center"), href=f"/playlists?id={p['playlist_id']}", action=True)


@callback(
    Output("pl-list", "children"),
    Input("pl-search", "value"),
    Input("pl-sort", "value"),
    Input("pl-deleted", "value"),
    State("cache-version", "data"),
)
def update_list(search, sort, include_deleted, cache_ver):
    items = playlist_overview((search or "").strip(), sort or "changed", bool(include_deleted), int(cache_ver or 0))
    if not items:
        return empty_state("Noch keine Playlists", "Der erste Abgleich läuft im Backend (stündlich).",
                           icon="bi bi-music-note-list")
    return [html.Small(f"{len(items)} Playlists", className="text-muted d-block mb-2"),
            dbc.ListGroup([_playlist_row(p) for p in items])]


# --- Detailansicht ---

def _change_row(c: dict):
    sym, color, label = OP_STYLE[c["op"]]
    item = c["new"] or c["old"]
    if c["op"] == "moved":
        pos = f"{c['old']['position'] + 1} → {c['new']['position'] + 1}"
    elif c["op"] == "replaced":
        pos = f"{c['new']['position'] + 1}"
    else:
        pos = f"{item['position'] + 1}"
    detail = item.get("artists") or ""
    if c["op"] == "replaced":
        detail += f" · {c['old']['track_id']} → {c['new']['track_id']}"
    return html.Tr([
        html.Td(dbc.Badge(sym, color=color, title=label), style={"width": "36px"}),
        html.Td(pos, className="text-muted text-nowrap", style={"width": "80px"}),
        html.Td([html.Span(item.get("name") or item.get("uri") or "?"),
                 html.Small(f" · {detail}" if detail else "", className="text-muted")]),
    ])


def _diff_view(changes: list[dict]):
    if not changes:
        return html.Div("Keine Unterschiede.", className="text-muted small")
    s = diff_summary(changes)
    head = html.Div([dbc.Badge(f"{OP_STYLE[op][0]} {s[op]} {OP_STYLE[op][2]}", color=OP_STYLE[op][1],
                               className="me-1") for op in OP_STYLE if s[op]], className="mb-2")
    more = html.Small(f"… und {len(changes) - DIFF_LIMIT} weitere", className="text-muted") \
        if len(changes) > DIFF_LIMIT else None
    return html.Div([head, dbc.Table(html.Tbody([_change_row(c) for c in changes[:DIFF_LIMIT]]), size="sm",
                                     className="mb-1"), more])


def _detail_layout(playlist_id: str):
    p = playlist_info(playlist_id)
    if not p:
        return empty_state("Playlist unbekannt", "Zurück zur Übersicht.", icon="bi bi-question-circle")
    snaps = snapshots(playlist_id)
    options = [{"label": f"{local_time(s['taken_at'])} · {s['track_count']} Titel · "
                         f"{REASON_LABELS.get(s['reason'], s['reason'])}", "value": s["id"]} for s in snaps]
    latest = snaps[0]["id"] if snaps else None
    previous = snaps[1]["id"] if len(snaps) > 1 else None
    return html.Div([
        dcc.Store(id="pl-id", data=playlist_id),
        dcc.Store(id="pl-pending"),
        dbc.Card(dbc.CardBody(html.Div([
            html.Div([
                html.A([html.I(className="bi bi-chevron-left me-1"), "Alle Playlists"], href="/playlists",
                       className="small d-block mb-1"),
                html.Span(p["name"], className="h5 me-2"),
                dbc.Badge("gelöscht", color="danger") if p["deleted_at"] else None,
                html.Small(f"{p['track_count'] or 0} Titel · {len(snaps)} Stände · zuletzt abgeglichen "
                           f"{local_time(p['last_synced_at'])}", className="text-muted d-block"),
            ]),
            html.Div([
                dbc.Button([html.I(className="bi bi-arrow-repeat me-1"), "Jetzt abgleichen"], id="pl-sync",
                           size="sm", color="secondary", outline=True, className="me-2"),
                dbc.Button([html.I(className="bi bi-arrow-left-right me-1"), "Ersetzte Versionen austauschen"],
                           id="pl-replace-open", size="sm", color="warning", outline=True),
            ]),
        ], className="d-flex justify-content-between align-items-start flex-wrap gap-2")), className="mb-3"),
        html.Div(id="pl-feedback"),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Verlauf"),
                dbc.CardBody(dbc.ListGroup([
                    dbc.ListGroupItem([
                        html.Div(local_time(s["taken_at"]), className="fw-semibold small"),
                        html.Small(f"{s['track_count']} Titel · {REASON_LABELS.get(s['reason'], s['reason'])}",
                                   className="text-muted"),
                    ], id={"type": "pl-snap", "id": s["id"]}, action=True, n_clicks=0)
                    for s in snaps[:100]
                ], flush=True), className="p-0", style={"maxHeight": "70vh", "overflowY": "auto"}),
            ]), md=4, className="mb-3"),
            dbc.Col(dbc.Card([
                dbc.CardHeader(dbc.Row([
                    dbc.Col(dbc.Select(id="pl-from", options=[{"label": "(leer)", "value": 0}] + options,
                                       value=previous or 0), md=5),
                    dbc.Col(html.Div("→", className="text-center"), md=1),
                    dbc.Col(dbc.Select(id="pl-to", options=options, value=latest), md=6),
                ], className="g-2 align-items-center")),
                dbc.CardBody([
                    dcc.Loading(html.Div(id="pl-diff")),
                    html.Hr(),
                    # Lieblingssongs haben keine Reihenfolge, die sich über die API setzen ließe.
                    # Button nur ausblenden: fehlt ein Input im Layout, feuert Dash den Callback gar nicht.
                    html.Small("Lieblingssongs lassen sich nicht zurücksetzen (Spotify sortiert sie nach "
                               "Hinzufüge-Datum).", className="text-muted")
                    if playlist_id == history.LIKED_ID else None,
                    dbc.Button([html.I(className="bi bi-arrow-counterclockwise me-1"),
                                "Playlist auf den rechten Stand zurücksetzen"],
                               id="pl-restore-open", size="sm", color="primary",
                               disabled=not (len(snaps) >= 2 or (p["deleted_at"] and snaps)),
                               style={"display": "none"} if playlist_id == history.LIKED_ID else None),
                ]),
            ]), md=8),
        ]),
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(id="pl-modal-title")),
            dbc.ModalBody(id="pl-modal-body", style={"maxHeight": "60vh", "overflowY": "auto"}),
            dbc.ModalFooter([
                dbc.Button("Abbrechen", id="pl-modal-cancel", color="secondary", outline=True),
                dbc.Button("Ausführen", id="pl-modal-confirm", color="primary"),
            ]),
        ], id="pl-modal", is_open=False, size="lg", centered=True),
    ])


def layout(id=None, **_kwargs):
    content = _detail_layout(id) if id else _overview_layout()
    return dbc.Container(content, fluid=True)


@callback(
    Output("pl-from", "value"),
    Output("pl-to", "value"),
    Input({"type": "pl-snap", "id": ALL}, "n_clicks"),
    State("pl-to", "options"),
    prevent_initial_call=True
)
def select_snapshot(_clicks, options):
    if not ctx.triggered or not ctx.triggered[0]["value"]:
        return no_update, no_update
    pk = ctx.triggered_id["id"]
    ids = [o["value"] for o in options]
    idx = ids.index(pk) if pk in ids else 0
    previous = ids[idx + 1] if idx + 1 < len(ids) else 0
    return previous, pk


@callback(
    Output("pl-diff", "children"),
    Input("pl-from", "value"),
    Input("pl-to", "value"),
)
def update_diff(old_pk, new_pk):
    if not new_pk:
        return html.Div("Noch kein Stand gespeichert.", className="text-muted small")
    return _diff_view(snapshot_diff(int(old_pk or 0), int(new_pk)))


@callback(
    Output("pl-modal", "is_open"),
    Output("pl-modal-title", "children"),
    Output("pl-modal-body", "children"),
    Output("pl-pending", "data"),
    Input("pl-restore-open", "n_clicks"),
    Input("pl-replace-open", "n_clicks"),
    Input("pl-modal-cancel", "n_clicks"),
    State("pl-id", "data"),
    State("pl-to", "value"),
    prevent_initial_call=True
)
def open_modal(_restore, _replace, _cancel, playlist_id, target_pk):
    if ctx.triggered_id == "pl-modal-cancel" or not ctx.triggered[0]["value"]:
        return False, no_update, no_update, None
    try:
        if ctx.triggered_id == "pl-restore-open":
            prev = actions.preview_restore(int(target_pk))
            body = [html.P("So ändert sich die Playlist gegenüber dem aktuellen Stand. Der aktuelle Stand wird "
                           "vorher gesichert und lässt sich wieder herstellen.", className="small"),
                    _diff_view(prev["changes"])]
            if prev["local_files"]:
                body.insert(0, dbc.Alert(f"{prev['local_files']} lokale Dateien können nicht wiederhergestellt "
                                         "werden.", color="warning"))
            return True, "Auf diesen Stand zurücksetzen?", body, \
                {"action": "restore", "snapshot": int(target_pk), "hash": prev["expected_hash"]}
        todo, digest = actions.superseded_items(playlist_id)
        if not todo:
            return True, "Ersetzte Versionen", html.Div("Keine ersetzten Versionen gefunden.",
                                                         className="text-muted"), None
        note = ("Die neuen Versionen landen bei den Lieblingssongs oben in der Liste (Spotify erlaubt kein "
                "Setzen des Datums)." if playlist_id == history.LIKED_ID else
                "Positionen bleiben erhalten; das Hinzufüge-Datum setzt Spotify neu.")
        rows = [html.Tr([html.Td(it["position"] + 1, className="text-muted"),
                         html.Td([html.Span(it["name"]), html.Small(f" · {it['artists']}", className="text-muted")]),
                         html.Td(html.Small(f"{it['track_id']} → {it['new_id']}", className="font-monospace"))])
                for it in todo]
        return True, f"{len(todo)} ersetzte Versionen austauschen?", \
            [html.P(note, className="small"), dbc.Table(html.Tbody(rows), size="sm")], \
            {"action": "replace", "playlist": playlist_id, "hash": digest}
    except actions.PlaylistActionError as e:
        return True, "Nicht möglich", dbc.Alert(str(e), color="warning"), None


@callback(
    Output("pl-feedback", "children"),
    Output("pl-modal", "is_open", allow_duplicate=True),
    Output("cache-version", "data", allow_duplicate=True),
    Input("pl-modal-confirm", "n_clicks"),
    Input("pl-sync", "n_clicks"),
    State("pl-pending", "data"),
    State("pl-id", "data"),
    prevent_initial_call=True
)
def run_action(_confirm, _sync, pending, playlist_id):
    if not ctx.triggered[0]["value"]:
        return no_update, no_update, no_update
    reload_hint = html.A(" Neu laden", href=f"/playlists?id={playlist_id}", className="alert-link")
    try:
        sp = spotify_client()
        if ctx.triggered_id == "pl-sync":
            changed = history.sync_playlist_by_id(sp, playlist_id)
            msg = "Neuer Stand gespeichert." if changed else "Keine Änderungen seit dem letzten Abgleich."
        elif not pending:
            return no_update, False, no_update
        elif pending["action"] == "restore":
            msg = actions.restore_snapshot(sp, pending["snapshot"], pending["hash"])
        else:
            msg = actions.replace_superseded(sp, pending["playlist"], pending["hash"])
    except actions.PlaylistActionError as e:
        return dbc.Alert(str(e), color="warning"), False, no_update
    except Exception as e:
        return dbc.Alert(f"Fehler: {e}", color="danger"), False, no_update
    return dbc.Alert([msg, reload_hint], color="success"), False, bump_data_version()
