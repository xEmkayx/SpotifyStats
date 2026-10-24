import math

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback, ctx, ALL, no_update, dash_table

from frontend_new.components.empty_state import empty_state
from frontend_new.core.data_version import bump_data_version
from frontend_new.services.versions import (
    KIND_LABELS, version_groups, suggestions, catalog_changes, catalog_status,
    merge_songs, split_song, remove_override, dismiss_suggestion
)

dash.register_page(__name__, path="/versions", name="Versionen", group="Analyse", order=25)

GROUP_PAGE_SIZE = 20
CHANGES_PAGE_SIZE = 50
SUGGESTION_LIMIT = 50

KIND_COLORS = {"replaced": "warning", "same_recording": "info", "manual": "secondary"}
ENTITY_LABELS = {"song": "Song", "artist": "Artist", "album": "Album"}


def _spotify_link(song_id: str):
    return html.A(song_id, href=f"https://open.spotify.com/track/{song_id}", target="_blank",
                  className="font-monospace small")


def _status_badge(member: dict):
    if member["kind"] is None:
        return dbc.Badge("kanonisch", color="success", className="me-1")
    badges = [dbc.Badge(KIND_LABELS[member["kind"]], color=KIND_COLORS[member["kind"]], className="me-1")]
    if member["available"] == 0 and not member["relinked_to"]:
        badges.append(dbc.Badge("nicht verfügbar", color="danger"))
    return html.Span(badges)


def _group_card(g: dict):
    canonical = next((m for m in g["members"] if m["kind"] is None), g["members"][0] if g["members"] else {})
    rows = []
    for m in g["members"]:
        album = m["album_name"] or "—"
        if m["album_type"]:
            album += f" ({m['album_type']}{', ' + m['release_date'][:4] if m['release_date'] else ''})"
        action = dbc.Button("Trennen", id={"type": "ver-split", "song": m["song_id"]}, size="sm",
                            color="secondary", outline=True) if m["kind"] is not None else None
        rows.append(html.Tr([
            html.Td(m["song_name"]), html.Td(album, className="text-muted"),
            html.Td(f"{m['plays']}", className="text-end"), html.Td(_status_badge(m)),
            html.Td(_spotify_link(m["song_id"])), html.Td(action),
        ]))
    return dbc.Card([
        dbc.CardHeader(html.Div([
            html.Div([html.Span(g["song_name"], className="fw-semibold"),
                      html.Small(f" · {canonical.get('artists', '')}", className="text-muted")]),
            html.Div([dbc.Badge(f"{g['versions']} Versionen", color="light", text_color="dark", className="me-1"),
                      dbc.Badge(f"{int(g['total_plays'])} Streams", color="primary")]),
        ], className="d-flex justify-content-between align-items-center flex-wrap gap-2")),
        dbc.CardBody(dbc.Table([
            html.Thead(html.Tr([html.Th("Titel"), html.Th("Album"), html.Th("Streams", className="text-end"),
                                html.Th("Status"), html.Th("Spotify-ID"), html.Th("")])),
            html.Tbody(rows),
        ], size="sm", hover=True, responsive=True, className="mb-0"), className="p-2"),
    ], className="mb-3")


def _suggestion_card(s: dict):
    a, b = s["a"], s["b"]

    def side(x, plays):
        return html.Div([
            html.Div(x["song_name"], className="fw-semibold"),
            html.Small(f"{x['artists']} · {x['album_name'] or '—'} ({x['album_type'] or '?'})",
                       className="text-muted d-block"),
            html.Small(f"{plays} Streams · {round(x['duration_ms'] / 1000)} s · ISRC {x['isrc'] or '—'}",
                       className="text-muted d-block"),
            _spotify_link(x["song_id"]),
        ])

    # Die meistgehörte Version wird zum Ziel; die kanonische Version berechnet die Gruppe ohnehin neu
    source, target = (a["song_id"], b["song_id"]) if s["plays_a"] <= s["plays_b"] else (b["song_id"], a["song_id"])
    return dbc.Card(dbc.CardBody(dbc.Row([
        dbc.Col(side(a, s["plays_a"]), md=5),
        dbc.Col(side(b, s["plays_b"]), md=5),
        dbc.Col([
            dbc.Button("Verbinden", id={"type": "ver-merge", "song": source, "target": target}, size="sm",
                       color="primary", className="w-100 mb-1"),
            dbc.Button("Ablehnen", id={"type": "ver-dismiss", "song": a["song_id"], "target": b["song_id"]},
                       size="sm", color="secondary", outline=True, className="w-100"),
        ], md=2),
    ], className="g-2 align-items-center"), className="p-2"), className="mb-2")


def _groups_tab():
    return html.Div([
        dbc.Row([
            dbc.Col(dbc.Input(id="ver-search", placeholder="Titel oder Artist suchen", debounce=True), md=5),
            dbc.Col(dbc.Select(id="ver-kind", value="all", options=[{"label": "Alle Arten", "value": "all"}] + [
                {"label": label, "value": k} for k, label in KIND_LABELS.items()]), md=3),
            dbc.Col(dbc.Select(id="ver-sort", value="plays", options=[
                {"label": "Sortieren: Streams", "value": "plays"},
                {"label": "Sortieren: Anzahl Versionen", "value": "versions"},
                {"label": "Sortieren: Titel", "value": "name"}]), md=4),
        ], className="g-2 mb-3"),
        dcc.Store(id="ver-page", data=0),
        dcc.Loading(html.Div(id="ver-groups")),
        html.Div([
            dbc.Button("‹ Zurück", id="ver-prev", size="sm", color="secondary", outline=True, className="me-2"),
            html.Span(id="ver-page-label", className="text-muted small me-2"),
            dbc.Button("Weiter ›", id="ver-next", size="sm", color="secondary", outline=True),
        ], className="d-flex align-items-center justify-content-center mt-2"),
    ], className="pt-3")


def _suggestions_tab():
    return html.Div([
        html.P("Gleicher Titel, gleiche Artists und ähnliche Dauer, aber keine eindeutige Verbindung "
               "(z. B. Remaster mit eigener ISRC). Wird nur nach Bestätigung verbunden.", className="text-muted small"),
        dbc.Input(id="ver-sugg-search", placeholder="Titel oder Artist filtern", debounce=True, className="mb-3"),
        dcc.Loading(html.Div(id="ver-suggestions")),
    ], className="pt-3")


def _changes_tab():
    return html.Div([
        dbc.Row([
            dbc.Col(dbc.Input(id="ver-chg-search", placeholder="Alter/neuer Wert oder ID", debounce=True), md=8),
            dbc.Col(dbc.Select(id="ver-chg-entity", value="all", options=[{"label": "Alle", "value": "all"}] + [
                {"label": v, "value": k} for k, v in ENTITY_LABELS.items()]), md=4),
        ], className="g-2 mb-3"),
        dash_table.DataTable(
            id="ver-changes",
            columns=[{"name": "Erkannt", "id": "detected_at"}, {"name": "Art", "id": "entity"},
                     {"name": "Feld", "id": "field"}, {"name": "Alt", "id": "old_value"},
                     {"name": "Neu", "id": "new_value"}, {"name": "Quelle", "id": "source"},
                     {"name": "ID", "id": "entity_id"}],
            data=[], page_current=0, page_size=CHANGES_PAGE_SIZE, page_count=1, page_action="custom",
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "6px", "backgroundColor": "transparent", "color": "inherit",
                        "border": "1px solid rgba(255,255,255,.08)", "maxWidth": "320px", "overflow": "hidden",
                        "textOverflow": "ellipsis"},
            style_header={"fontWeight": "600", "backgroundColor": "rgba(255,255,255,.04)"},
        ),
    ], className="pt-3")


def _manual_tab(overrides):
    return html.Div([
        dbc.Card(dbc.CardBody([
            html.Div("Songs von Hand verbinden", className="fw-semibold mb-2"),
            dbc.Row([
                dbc.Col(dbc.Input(id="ver-merge-source", placeholder="Song-ID (wird zugeordnet)"), md=5),
                dbc.Col(dbc.Input(id="ver-merge-target", placeholder="gehört zu Song-ID"), md=5),
                dbc.Col(dbc.Button("Verbinden", id="ver-merge-manual", color="primary", className="w-100"), md=2),
            ], className="g-2"),
        ]), className="mb-3"),
        html.Div("Manuelle Entscheidungen", className="fw-semibold mb-2"),
        html.Div(id="ver-overrides", children=overrides),
    ], className="pt-3")


def layout():
    # Status direkt beim Seitenaufbau rendern: ein Callback, der nur an ver-refresh hängt,
    # wird von Dash verworfen, wenn handle_action beim Rendern der Buttons kurz mitläuft
    status, overrides = _status_children()
    return dbc.Container([
        dcc.Store(id="ver-refresh", data=0),
        html.Div(id="ver-feedback"),
        dbc.Card(dbc.CardBody(html.Div(id="ver-status", children=status)), className="mb-3"),
        dbc.Tabs([
            dbc.Tab(_groups_tab(), label="Versionen", tab_id="groups"),
            dbc.Tab(_suggestions_tab(), label="Vorschläge", tab_id="suggestions"),
            dbc.Tab(_changes_tab(), label="Änderungen", tab_id="changes"),
            dbc.Tab(_manual_tab(overrides), label="Manuell", tab_id="manual"),
        ], active_tab="groups", class_name="tabs-minimal"),
    ], fluid=True)


@callback(
    Output("ver-status", "children"),
    Output("ver-overrides", "children"),
    Input("ver-refresh", "data"),
    prevent_initial_call=True
)
def update_status(_):
    return _status_children()


def _status_children():
    s = catalog_status()
    kinds = s["kinds"]
    status = html.Div([
        html.Div([
            html.Span(f"{s['groups']} Lieder mit mehreren Versionen", className="fw-semibold me-3"),
            *[dbc.Badge(f"{KIND_LABELS[k]}: {kinds.get(k, 0)}", color=KIND_COLORS[k], className="me-1")
              for k in KIND_LABELS],
        ], className="mb-2"),
        html.Small(f"Katalog geprüft: {s['checked'] or 0} von {s['songs']} Songs · mit ISRC: {s['with_isrc'] or 0} · "
                   f"ersetzt: {s['relinked'] or 0} · nicht verfügbar: {s['dead'] or 0}", className="text-muted d-block"),
        *[html.Small(f"{name}: {value}", className="text-muted d-block") for name, value in sorted(s["state"].items())],
    ])
    if not s["overrides"]:
        overrides = html.Div("Keine manuellen Entscheidungen.", className="text-muted small")
    else:
        overrides = dbc.ListGroup([dbc.ListGroupItem(html.Div([
            html.Div([
                html.Span(o["song_name"] or o["song_id"]),
                html.Small(f" → {o['target_name'] or o['target_song_id']}" if o["target_song_id"]
                           else " · nie automatisch verbinden", className="text-muted"),
            ]),
            dbc.Button("Aufheben", id={"type": "ver-unoverride", "song": o["song_id"]}, size="sm",
                       color="secondary", outline=True),
        ], className="d-flex justify-content-between align-items-center")) for o in s["overrides"]])
    return status, overrides


@callback(
    Output("ver-page", "data"),
    Input("ver-prev", "n_clicks"),
    Input("ver-next", "n_clicks"),
    Input("ver-search", "value"),
    Input("ver-kind", "value"),
    Input("ver-sort", "value"),
    State("ver-page", "data"),
    prevent_initial_call=True
)
def change_page(_prev, _next, _search, _kind, _sort, page):
    if ctx.triggered_id == "ver-prev":
        return max(0, (page or 0) - 1)
    if ctx.triggered_id == "ver-next":
        return (page or 0) + 1
    return 0  # neue Filter -> erste Seite


@callback(
    Output("ver-groups", "children"),
    Output("ver-page-label", "children"),
    Input("ver-page", "data"),
    Input("ver-refresh", "data"),
    State("ver-search", "value"),
    State("ver-kind", "value"),
    State("ver-sort", "value"),
    State("cache-version", "data"),
)
def update_groups(page, _refresh, search, kind, sort, cache_ver):
    result = version_groups((search or "").strip(), kind or "all", sort or "plays", int(page or 0),
                            GROUP_PAGE_SIZE, int(cache_ver or 0))
    pages = max(1, math.ceil(result["total"] / GROUP_PAGE_SIZE))
    label = f"Seite {min(int(page or 0) + 1, pages)} von {pages} · {result['total']} Gruppen"
    if not result["groups"]:
        return empty_state("Keine Versionen gefunden", "Suche oder Filter anpassen.", icon="bi bi-layers"), label
    return [_group_card(g) for g in result["groups"]], label


@callback(
    Output("ver-suggestions", "children"),
    Input("ver-sugg-search", "value"),
    Input("ver-refresh", "data"),
    State("cache-version", "data"),
)
def update_suggestions(search, _refresh, cache_ver):
    items = suggestions((search or "").strip(), int(cache_ver or 0))
    if not items:
        return empty_state("Keine Vorschläge", "Alle eindeutigen Fälle sind bereits verbunden.", icon="bi bi-check2-all")
    head = html.Small(f"{len(items)} Vorschläge" + (f", die ersten {SUGGESTION_LIMIT} angezeigt"
                                                    if len(items) > SUGGESTION_LIMIT else ""),
                      className="text-muted d-block mb-2")
    return [head] + [_suggestion_card(s) for s in items[:SUGGESTION_LIMIT]]


@callback(
    Output("ver-changes", "data"),
    Output("ver-changes", "page_count"),
    Input("ver-changes", "page_current"),
    Input("ver-chg-search", "value"),
    Input("ver-chg-entity", "value"),
    Input("ver-refresh", "data"),
    State("cache-version", "data"),
)
def update_changes(page, search, entity, _refresh, cache_ver):
    if ctx.triggered_id in ("ver-chg-search", "ver-chg-entity"):
        page = 0
    result = catalog_changes((search or "").strip(), entity or "all", int(page or 0), CHANGES_PAGE_SIZE,
                             int(cache_ver or 0))
    df = result["rows"]
    if not df.empty:
        df["entity"] = df["entity"].map(ENTITY_LABELS).fillna(df["entity"])
    return df.to_dict("records"), max(1, math.ceil(result["total"] / CHANGES_PAGE_SIZE))


@callback(
    Output("ver-feedback", "children"),
    Output("ver-refresh", "data"),
    Output("cache-version", "data", allow_duplicate=True),
    Input({"type": "ver-split", "song": ALL}, "n_clicks"),
    Input({"type": "ver-merge", "song": ALL, "target": ALL}, "n_clicks"),
    Input({"type": "ver-dismiss", "song": ALL, "target": ALL}, "n_clicks"),
    Input({"type": "ver-unoverride", "song": ALL}, "n_clicks"),
    Input("ver-merge-manual", "n_clicks"),
    State("ver-merge-source", "value"),
    State("ver-merge-target", "value"),
    State("ver-refresh", "data"),
    prevent_initial_call=True
)
def handle_action(_split, _merge, _dismiss, _unoverride, _manual, source, target, refresh):
    # Neu gerenderte Buttons lösen den Callback mit n_clicks=None aus -> ignorieren
    if not ctx.triggered or not ctx.triggered[0]["value"]:
        return no_update, no_update, no_update
    trg = ctx.triggered_id
    if trg == "ver-merge-manual":
        msg = merge_songs(source, target)
        text = "Songs verbunden." if msg == "ok" else msg
    elif trg["type"] == "ver-split":
        split_song(trg["song"])
        msg, text = "ok", "Version abgetrennt. Sie wird nicht mehr automatisch verbunden."
    elif trg["type"] == "ver-merge":
        msg = merge_songs(trg["song"], trg["target"])
        text = "Vorschlag übernommen." if msg == "ok" else msg
    elif trg["type"] == "ver-dismiss":
        msg, text = dismiss_suggestion(trg["song"], trg["target"]), "Vorschlag abgelehnt."
    else:
        msg, text = remove_override(trg["song"]), "Manuelle Entscheidung aufgehoben."
    if msg != "ok":
        return dbc.Alert(text, color="warning", duration=5000), no_update, no_update
    # Neue Datenversion -> alle gecachten Statistiken rechnen mit den neuen Gruppen
    return dbc.Alert(text, color="success", duration=4000), (refresh or 0) + 1, bump_data_version()
