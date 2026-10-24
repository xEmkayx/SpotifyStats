from urllib.parse import parse_qs

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback, ctx, ALL, no_update, dash_table

from common import settings
from common.playlists import actions, bulk, history
from frontend_new.components.empty_state import empty_state
from frontend_new.core.data_version import bump_data_version
from frontend_new.services.playlists import (
    playlist_overview, playlist_info, snapshots, snapshot_diff, diff_summary, local_time, count
)
from frontend_new.services.spotify_images import spotify_client, library_write_allowed

dash.register_page(__name__, path="/playlists", name="Playlists", group="Bibliothek", order=30)

OP_STYLE = {
    "added": ("+", "success", "neu"),
    "removed": ("−", "danger", "entfernt"),
    "moved": ("↕", "info", "verschoben"),
    "replaced": ("⇄", "warning", "neue Version"),
}
REASON_LABELS = {"initial": "zum ersten Mal gespeichert", "sync": "geändert", "manual": "von dir geprüft",
                 "before_restore": "Sicherung vor dem Wiederherstellen", "restore": "wiederhergestellt",
                 "before_replace": "Sicherung vor dem Austauschen", "replace": "Versionen ausgetauscht"}
DIFF_LIMIT = 300


def _playlist_id_from_search(search: str):
    return (parse_qs((search or "").lstrip("?")).get("id") or [None])[0]


# --- Übersicht ---

def _overview_layout():
    return html.Div([
        dbc.Row([
            dbc.Col(dbc.Input(id="pl-search", placeholder="Playlist suchen", debounce=True), md=5),
            dbc.Col(dbc.Select(id="pl-sort", value="changed", options=[
                {"label": "Zuletzt geändert", "value": "changed"},
                {"label": "Name A–Z", "value": "name"},
                {"label": "Meiste Songs", "value": "tracks"},
                {"label": "Meiste Songs mit neuerer Version", "value": "superseded"}]), md=4),
            dbc.Col(dbc.Checkbox(id="pl-deleted", label="Gelöschte Playlists anzeigen", value=False), md=3,
                    className="d-flex align-items-center"),
        ], className="g-2 mb-3"),
        html.Small("Hier siehst du deine eigenen Playlists. Playlists von Spotify oder anderen Leuten sind nicht "
                   "dabei. Änderungen werden jede Stunde gespeichert.", className="text-muted d-block mb-3"),
        html.Div(id="pl-feedback-overview", className="toast-area"),
        dcc.Store(id="pl-bulk-refresh", data=0),
        dcc.Interval(id="pl-bulk-poll", interval=3000, disabled=False),
        html.Div(id="pl-bulk-info"),
        dcc.Loading(html.Div(id="pl-list"), delay_show=600),
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Veraltete Versionen austauschen")),
            dbc.ModalBody([
                html.P("Spotify hat diese Songs durch eine neuere Version ersetzt. Beim Austauschen bleibt jeder Song "
                       "an seiner Stelle; vorher wird der aktuelle Stand jeder Playlist gespeichert, damit du im "
                       "Verlauf siehst, was sich geändert hat.", className="small"),
                html.Div([
                    dbc.Button("Alle", id="pl-bulk-all", size="sm", color="secondary", outline=True, className="me-1"),
                    dbc.Button("Keine", id="pl-bulk-none", size="sm", color="secondary", outline=True),
                ], className="mb-2"),
                dbc.Checklist(id="pl-bulk-select", options=[], value=[], className="select-list"),
            ]),
            dbc.ModalFooter([
                dbc.Button("Abbrechen", id="pl-bulk-cancel", color="secondary", outline=True),
                dbc.Button("Austauschen", id="pl-bulk-confirm", color="primary"),
            ]),
        ], id="pl-bulk-modal", is_open=False, size="lg", centered=True),
    ])


def _playlist_row(p: dict):
    badges = []
    if p["deleted_at"]:
        badges.append(dbc.Badge("gelöscht", color="danger", className="me-1"))
    if p["superseded"]:
        badges.append(dbc.Badge(count(p["superseded"], "Song mit neuerer Version", "Songs mit neuerer Version"),
                                color="warning", className="me-1",
                                title="Noch nicht ausgetauscht – das passiert erst, wenn du es auslöst oder "
                                      "in den Einstellungen automatisch einschaltest."))
    img = html.Img(src=p["image_url"], style={"width": "48px", "height": "48px", "objectFit": "cover",
                                             "borderRadius": "6px"}) if p["image_url"] else \
        html.Div(html.I(className="bi bi-music-note-list"), className="text-muted",
                 style={"width": "48px", "height": "48px", "display": "flex", "alignItems": "center",
                        "justifyContent": "center", "fontSize": "22px"})
    return dbc.ListGroupItem(html.Div([
        img,
        html.Div([
            html.Div([html.Span(p["name"] or p["playlist_id"], className="fw-semibold me-2"), *badges]),
            html.Small(f"{count(p['track_count'], 'Song', 'Songs')} · "
                       f"{count(p['snapshots'], 'gespeicherter Stand', 'gespeicherte Stände')} · geändert am "
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
        return empty_state("Noch keine Playlists", "Deine Playlists werden beim nächsten stündlichen Abgleich geladen.",
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
        return empty_state("Diese Playlist gibt es hier nicht", "Zurück zur Übersicht.", icon="bi bi-question-circle")
    snaps = snapshots(playlist_id)
    options = [{"label": f"{local_time(s['taken_at'])} · {count(s['track_count'], 'Song', 'Songs')} · "
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
                html.Small(f"{count(p['track_count'], 'Song', 'Songs')} · "
                           f"{count(len(snaps), 'gespeicherter Stand', 'gespeicherte Stände')} · zuletzt geprüft "
                           f"am {local_time(p['last_synced_at'])}", className="text-muted d-block"),
            ]),
            html.Div([
                dbc.Button([html.I(className="bi bi-arrow-repeat me-1"), "Jetzt prüfen"], id="pl-sync",
                           size="sm", color="secondary", outline=True, className="me-2"),
                dbc.Button([html.I(className="bi bi-arrow-left-right me-1"), "Veraltete Versionen austauschen"],
                           id="pl-replace-open", size="sm", color="warning", outline=True),
            ]),
        ], className="d-flex justify-content-between align-items-start flex-wrap gap-2")), className="mb-3"),
        html.Div(id="pl-feedback", className="toast-area"),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Verlauf"),
                dbc.CardBody(dbc.ListGroup([
                    dbc.ListGroupItem([
                        html.Div(local_time(s["taken_at"]), className="fw-semibold small"),
                        html.Small(f"{count(s['track_count'], 'Song', 'Songs')} · "
                                   f"{REASON_LABELS.get(s['reason'], s['reason'])}",
                                   className="text-muted"),
                    ], id={"type": "pl-snap", "id": s["id"]}, action=True, n_clicks=0)
                    for s in snaps[:100]
                ], flush=True), className="p-0", style={"maxHeight": "70vh", "overflowY": "auto"}),
            ]), md=4, className="mb-3"),
            dbc.Col(dbc.Card([
                dbc.CardHeader(dbc.Row([
                    dbc.Col(dbc.Select(id="pl-from", options=[{"label": "Leere Playlist", "value": 0}] + options,
                                       value=previous or 0), md=5),
                    dbc.Col(html.Div("→", className="text-center"), md=1),
                    dbc.Col(dbc.Select(id="pl-to", options=options, value=latest), md=6),
                ], className="g-2 align-items-center")),
                dbc.CardBody([
                    dcc.Loading(html.Div(id="pl-diff")),
                    html.Hr(),
                    # Lieblingssongs haben keine Reihenfolge, die sich über die API setzen ließe.
                    # Button nur ausblenden: fehlt ein Input im Layout, feuert Dash den Callback gar nicht.
                    html.Small("Lieblingssongs lassen sich nicht zurücksetzen, weil Spotify sie immer nach dem "
                               "Datum sortiert, an dem du sie gespeichert hast.", className="text-muted")
                    if playlist_id == history.LIKED_ID else None,
                    dbc.Button([html.I(className="bi bi-arrow-counterclockwise me-1"),
                                "Rechten Stand wiederherstellen"],
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
                dbc.Button("Ja, mach das", id="pl-modal-confirm", color="primary"),
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
            body = [html.P("So ändert sich deine Playlist im Vergleich zu jetzt. Der aktuelle Stand wird vorher "
                           "gespeichert, du kannst also jederzeit zurück.", className="small"),
                    _diff_view(prev["changes"])]
            if prev["local_files"]:
                body.insert(0, dbc.Alert(f"{prev['local_files']} lokale Dateien kann Spotify nicht wieder "
                                         "einfügen, die fehlen danach.", color="warning"))
            return True, "Diesen Stand wiederherstellen?", body, \
                {"action": "restore", "snapshot": int(target_pk), "hash": prev["expected_hash"]}
        todo, digest = actions.superseded_items(playlist_id)
        if not todo:
            return True, "Alles aktuell", html.Div("Hier gibt es keine veralteten Versionen.",
                                                    className="text-muted"), None
        note = ("Die neuen Versionen erscheinen bei deinen Lieblingssongs ganz oben, weil Spotify das "
                "ursprüngliche Datum nicht übernehmen kann." if playlist_id == history.LIKED_ID else
                "Die Songs bleiben an derselben Stelle. Nur das Hinzufüge-Datum setzt Spotify neu.")
        options = [{"label": f"Platz {it['position'] + 1} · {it['name']} · {it['artists']}", "value": it["position"]}
                   for it in todo]
        body = [
            html.P(note + " Abgewählte Songs bleiben, wie sie sind.", className="small"),
            html.Div([
                dbc.Button("Alle", id={"type": "pl-replace-toggle", "mode": "all"}, size="sm", color="secondary",
                           outline=True, className="me-1"),
                dbc.Button("Keine", id={"type": "pl-replace-toggle", "mode": "none"}, size="sm", color="secondary",
                           outline=True),
            ], className="mb-2"),
            dbc.Checklist(id={"type": "pl-replace-select", "n": 0}, options=options,
                          value=[o["value"] for o in options], className="select-list"),
        ]
        return True, f"{count(len(todo), 'Song hat', 'Songs haben')} eine neuere Version", body, \
            {"action": "replace", "playlist": playlist_id, "hash": digest}
    except actions.PlaylistActionError as e:
        return True, "Das geht leider nicht", dbc.Alert(str(e), color="warning"), None


@callback(
    Output("pl-feedback", "children"),
    Output("pl-modal", "is_open", allow_duplicate=True),
    Output("cache-version", "data", allow_duplicate=True),
    Input("pl-modal-confirm", "n_clicks"),
    Input("pl-sync", "n_clicks"),
    State("pl-pending", "data"),
    State("pl-id", "data"),
    State({"type": "pl-replace-select", "n": ALL}, "value"),
    prevent_initial_call=True
)
def run_action(_confirm, _sync, pending, playlist_id, selected):
    if not ctx.triggered[0]["value"]:
        return no_update, no_update, no_update
    reload_hint = html.A(" Seite neu laden", href=f"/playlists?id={playlist_id}", className="alert-link")
    try:
        sp = spotify_client()
        if ctx.triggered_id == "pl-sync":
            changed = history.sync_playlist_by_id(sp, playlist_id)
            msg = "Neuer Stand gespeichert." if changed else "Seit der letzten Prüfung hat sich nichts geändert."
        elif not pending:
            return no_update, False, no_update
        elif pending["action"] == "restore":
            msg = actions.restore_snapshot(sp, pending["snapshot"], pending["hash"])
        else:
            positions = selected[0] if selected else None
            if positions is not None and not positions:
                return dbc.Alert("Du hast keinen Song ausgewählt.", color="info", duration=3000), False, no_update
            msg = actions.replace_superseded(sp, pending["playlist"], pending["hash"], positions)
    except (actions.PlaylistActionError, RuntimeError) as e:
        # Verständliche Meldungen (z. B. fehlende Spotify-Verbindung) ohne Zusatz anzeigen
        return dbc.Alert(str(e), color="warning", dismissable=True), False, no_update
    except Exception as e:
        return dbc.Alert(f"Da ist etwas schiefgegangen: {e}", color="danger", dismissable=True), False, no_update
    return dbc.Alert([msg, reload_hint], color="success", dismissable=True), False, bump_data_version()


@callback(
    Output({"type": "pl-replace-select", "n": ALL}, "value"),
    Input({"type": "pl-replace-toggle", "mode": ALL}, "n_clicks"),
    State({"type": "pl-replace-select", "n": ALL}, "options"),
    prevent_initial_call=True
)
def toggle_replace_selection(_clicks, options):
    if not ctx.triggered or not ctx.triggered[0]["value"]:
        return [no_update] * len(options)
    select_all = ctx.triggered_id["mode"] == "all"
    return [[o["value"] for o in opts] if select_all else [] for opts in options]


# --- Sammelaustausch in der Übersicht ---

def _bulk_status_line():
    value, updated = bulk.status()
    if not value:
        return None
    running = bulk.is_running()
    if not running and value.startswith("läuft"):
        value = "wurde unterbrochen (" + value + ")"
    icon = "bi bi-arrow-repeat" if running else "bi bi-check2-circle"
    return html.Small([html.I(className=f"{icon} me-1"),
                       f"Austausch {value}" + ("" if running else f" ({local_time(updated)})")],
                      className="text-muted d-block mt-1")


@callback(
    Output("pl-bulk-info", "children"),
    Output("pl-bulk-poll", "disabled"),
    Input("pl-bulk-poll", "n_intervals"),
    Input("pl-bulk-refresh", "data"),
)
def update_bulk_info(_n, _refresh):
    overview = bulk.superseded_overview()
    total = sum(p["superseded"] for p in overview)
    auto = settings.get_flag(settings.AUTO_REPLACE_PLAYLISTS)
    auto_text = ("Neue veraltete Versionen werden automatisch ausgetauscht. " if auto else
                 "Automatisch austauschen kannst du in den ")
    running = bulk.is_running()
    if not total and not running:
        return None, True
    info = dbc.Card(dbc.CardBody(html.Div([
        html.Div([
            html.Div(f"{count(total, 'Song', 'Songs')} in {count(len(overview), 'Playlist', 'Playlists')} "
                     f"{'hat' if total == 1 else 'haben'} eine neuere Version.", className="fw-semibold"),
            html.Small([auto_text, html.A("Einstellungen", href="/settings") if not auto else
                        html.A("Einstellung ändern", href="/settings"), "" if auto else " einschalten."],
                       className="text-muted d-block"),
            _bulk_status_line(),
        ]),
        dbc.Button("Austauschen …", id="pl-bulk-open", color="warning", outline=True, size="sm",
                   disabled=running),
    ], className="d-flex justify-content-between align-items-start gap-3 flex-wrap"), className="py-2"),
        className="mb-3")
    return info, not running


@callback(
    Output("pl-bulk-modal", "is_open"),
    Output("pl-bulk-select", "options"),
    Output("pl-bulk-select", "value"),
    Input("pl-bulk-open", "n_clicks"),
    Input("pl-bulk-cancel", "n_clicks"),
    Input("pl-bulk-all", "n_clicks"),
    Input("pl-bulk-none", "n_clicks"),
    State("pl-bulk-select", "options"),
    prevent_initial_call=True
)
def bulk_modal(_open, _cancel, _all, _none, options):
    if not ctx.triggered or not ctx.triggered[0]["value"]:
        return no_update, no_update, no_update
    if ctx.triggered_id == "pl-bulk-cancel":
        return False, no_update, no_update
    if ctx.triggered_id in ("pl-bulk-all", "pl-bulk-none"):
        selectable = [o["value"] for o in options if not o.get("disabled")]
        return no_update, no_update, selectable if ctx.triggered_id == "pl-bulk-all" else []
    liked_ok = library_write_allowed()
    options = []
    for p in bulk.superseded_overview():
        disabled = p["playlist_id"] == history.LIKED_ID and not liked_ok
        label = f"{p['name']} · {count(p['superseded'], 'Song', 'Songs')}"
        if disabled:
            label += " (dafür fehlt noch eine Spotify-Berechtigung)"
        options.append({"label": label, "value": p["playlist_id"], "disabled": disabled})
    return True, options, [o["value"] for o in options if not o["disabled"]]


@callback(
    Output("pl-feedback-overview", "children"),
    Output("pl-bulk-modal", "is_open", allow_duplicate=True),
    Output("pl-bulk-refresh", "data"),
    Input("pl-bulk-confirm", "n_clicks"),
    State("pl-bulk-select", "value"),
    State("pl-bulk-refresh", "data"),
    prevent_initial_call=True
)
def bulk_confirm(_n, selected, refresh):
    if not selected:
        return dbc.Alert("Du hast keine Playlist ausgewählt.", color="info", duration=3000), no_update, no_update
    try:
        started = bulk.replace_many_in_background(spotify_client(), list(selected))
    except RuntimeError as e:
        return dbc.Alert(str(e), color="warning", dismissable=True), False, no_update
    except Exception as e:
        return dbc.Alert(f"Da ist etwas schiefgegangen: {e}", color="danger", dismissable=True), False, no_update
    if not started:
        return dbc.Alert("Es läuft schon ein Austausch.", color="info", duration=4000), False, no_update
    return dbc.Alert(f"Los geht's – {count(len(selected), 'Playlist wird', 'Playlists werden')} im Hintergrund "
                     "aktualisiert. Den Fortschritt siehst du oben.", color="success", duration=5000), \
        False, (refresh or 0) + 1
