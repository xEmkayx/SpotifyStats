import math

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback, ctx, ALL, no_update, dash_table

from frontend_new.components.empty_state import empty_state
from frontend_new.core.data_version import bump_data_version
from frontend_new.services.playlists import local_time, count
from frontend_new.services.versions import (
    KIND_LABELS, version_groups, suggestions, catalog_changes, catalog_status,
    merge_songs, split_song, remove_override, dismiss_suggestion, merge_many, dismiss_many
)

dash.register_page(__name__, path="/versions", name="Versionen", group="Bibliothek", order=31)

GROUP_PAGE_SIZE = 20
CHANGES_PAGE_SIZE = 50
SUGGESTION_PAGE_SIZE = 25

KIND_COLORS = {"replaced": "warning", "same_recording": "info", "manual": "secondary"}
KIND_FILTER_LABELS = {"replaced": "Veraltete Versionen", "same_recording": "Weitere Releases",
                      "manual": "Von dir verbunden"}
ENTITY_LABELS = {"song": "Song", "artist": "Artist", "album": "Album"}
ALBUM_TYPES = {"album": "Album", "single": "Single", "compilation": "Compilation"}
FIELD_LABELS = {"name": "Name", "album_id": "Album", "isrc": "ISRC", "relinked_to": "ersetzt durch",
                "available": "Verfügbarkeit"}
SOURCE_LABELS = {"import": "beim Hören", "sync": "Abgleich"}
SYNC_LABELS = {"catalog_full_status": "Kompletter Abgleich", "catalog_rolling_status": "Nächtlicher Abgleich"}


def _spotify_link(song_id: str):
    return html.A(song_id, href=f"https://open.spotify.com/track/{song_id}", target="_blank",
                  className="font-monospace small", title="In Spotify öffnen")


def _album_label(name, album_type, release_date) -> str:
    details = [d for d in (ALBUM_TYPES.get(album_type, album_type), (release_date or "")[:4]) if d]
    return f"{name or '—'}" + (f" ({', '.join(details)})" if details else "")


def _duration(ms) -> str:
    sec = round((ms or 0) / 1000)
    return f"{sec // 60}:{sec % 60:02d}"


def _status_badge(member: dict):
    if member["kind"] is None:
        return dbc.Badge("Hauptversion", color="success", className="me-1",
                         title="Unter dieser Version werden alle Streams gezählt")
    badges = [dbc.Badge(KIND_LABELS[member["kind"]], color=KIND_COLORS[member["kind"]], className="me-1")]
    if member["available"] == 0 and not member["relinked_to"]:
        badges.append(dbc.Badge("nicht mehr auf Spotify", color="danger"))
    return html.Span(badges)


def _group_card(g: dict):
    canonical = next((m for m in g["members"] if m["kind"] is None), g["members"][0] if g["members"] else {})
    rows = []
    for m in g["members"]:
        album = _album_label(m["album_name"], m["album_type"], m["release_date"])
        action = dbc.Button("Getrennt zählen", id={"type": "ver-split", "song": m["song_id"]}, size="sm",
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
            html.Div([dbc.Badge(count(g["versions"], "Version", "Versionen"), color="light", text_color="dark",
                                className="me-1"),
                      dbc.Badge(count(g["total_plays"], "Stream", "Streams") + " insgesamt", color="primary")]),
        ], className="d-flex justify-content-between align-items-center flex-wrap gap-2")),
        dbc.CardBody(dbc.Table([
            html.Thead(html.Tr([html.Th("Titel"), html.Th("Erschienen auf"), html.Th("Streams", className="text-end"),
                                html.Th(""), html.Th("ID"), html.Th("")])),
            html.Tbody(rows),
        ], size="sm", hover=True, responsive=True, className="mb-0"), className="p-2"),
    ], className="mb-3")


def _suggestion_card(s: dict):
    a, b = s["a"], s["b"]

    def side(x, plays):
        return html.Div([
            html.Div(x["song_name"], className="fw-semibold"),
            html.Small(f"{x['artists']} · {_album_label(x['album_name'], x['album_type'], None)}",
                       className="text-muted d-block"),
            html.Small(f"{count(plays, 'Stream', 'Streams')} · {_duration(x['duration_ms'])} min",
                       className="text-muted d-block"),
            _spotify_link(x["song_id"]),
        ])

    # Die meistgehörte Version wird zum Ziel; die Hauptversion berechnet die Gruppe ohnehin neu
    source, target = (a["song_id"], b["song_id"]) if s["plays_a"] <= s["plays_b"] else (b["song_id"], a["song_id"])
    return dbc.Card(dbc.CardBody(dbc.Row([
        dbc.Col(dbc.Checkbox(id={"type": "ver-sugg-check", "song": source, "target": target}, value=False),
                width="auto", className="pt-1"),
        dbc.Col(side(a, s["plays_a"]), md=5),
        dbc.Col(side(b, s["plays_b"]), md=4),
        dbc.Col([
            dbc.Button("Zusammen zählen", id={"type": "ver-merge", "song": source, "target": target}, size="sm",
                       color="primary", className="w-100 mb-1"),
            dbc.Button("Gehören nicht zusammen", id={"type": "ver-dismiss", "song": a["song_id"],
                                                    "target": b["song_id"]},
                       size="sm", color="secondary", outline=True, className="w-100"),
        ], md=2),
    ], className="g-2 align-items-center"), className="p-2"), className="mb-2")


def _groups_tab():
    return html.Div([
        dbc.Row([
            dbc.Col(dbc.Input(id="ver-search", placeholder="Song oder Artist suchen", debounce=True), md=5),
            dbc.Col(dbc.Select(id="ver-kind", value="all", options=[{"label": "Alle", "value": "all"}] + [
                {"label": label, "value": k} for k, label in KIND_FILTER_LABELS.items()]), md=3),
            dbc.Col(dbc.Select(id="ver-sort", value="plays", options=[
                {"label": "Meiste Streams zuerst", "value": "plays"},
                {"label": "Meiste Versionen zuerst", "value": "versions"},
                {"label": "Titel A–Z", "value": "name"}]), md=4),
        ], className="g-2 mb-3"),
        dcc.Store(id="ver-page", data=0),
        dcc.Loading(html.Div(id="ver-groups"), delay_show=600),
        html.Div([
            dbc.Button("‹ Zurück", id="ver-prev", size="sm", color="secondary", outline=True, className="me-2"),
            html.Span(id="ver-page-label", className="text-muted small me-2"),
            dbc.Button("Weiter ›", id="ver-next", size="sm", color="secondary", outline=True),
        ], className="d-flex align-items-center justify-content-center mt-2"),
    ], className="pt-3")


def _suggestions_tab():
    return html.Div([
        html.P("Diese Songs heißen gleich, sind vom selben Artist und fast gleich lang. Spotify führt sie aber "
               "als unterschiedliche Aufnahmen, zum Beispiel bei einem Remaster. Ob sie zusammengehören, "
               "entscheidest du.", className="text-muted small"),
        dbc.Input(id="ver-sugg-search", placeholder="Song oder Artist suchen", debounce=True, className="mb-3"),
        html.Div([
            dbc.Checkbox(id="ver-sugg-all", label="Alle auf dieser Seite auswählen", value=False,
                         className="me-3"),
            dbc.Button("Ausgewählte zusammen zählen", id="ver-sugg-merge-selected", size="sm", color="primary",
                       className="me-2"),
            dbc.Button("Ausgewählte gehören nicht zusammen", id="ver-sugg-dismiss-selected", size="sm",
                       color="secondary", outline=True),
        ], className="d-flex align-items-center flex-wrap gap-2 mb-3"),
        dcc.Store(id="ver-sugg-page", data=0),
        dcc.Loading(html.Div(id="ver-suggestions"), delay_show=600),
        html.Div([
            dbc.Button("‹ Zurück", id="ver-sugg-prev", size="sm", color="secondary", outline=True, className="me-2"),
            html.Span(id="ver-sugg-page-label", className="text-muted small me-2"),
            dbc.Button("Weiter ›", id="ver-sugg-next", size="sm", color="secondary", outline=True),
        ], className="d-flex align-items-center justify-content-center mt-2"),
    ], className="pt-3")


def _changes_tab():
    return html.Div([
        dbc.Row([
            dbc.Col(dbc.Input(id="ver-chg-search", placeholder="Name oder ID suchen", debounce=True), md=8),
            dbc.Col(dbc.Select(id="ver-chg-entity", value="all", options=[
                {"label": "Alles", "value": "all"}, {"label": "Songs", "value": "song"},
                {"label": "Artists", "value": "artist"}, {"label": "Alben", "value": "album"}]), md=4),
        ], className="g-2 mb-3"),
        dash_table.DataTable(
            id="ver-changes",
            columns=[{"name": "Wann", "id": "detected_at"}, {"name": "Was", "id": "entity"},
                     {"name": "Geändert", "id": "field"}, {"name": "Vorher", "id": "old_value"},
                     {"name": "Nachher", "id": "new_value"}, {"name": "Erkannt", "id": "source"},
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
            html.Div("Zwei Songs zusammen zählen", className="fw-semibold mb-1"),
            html.Small("Die ID steht in der Spotify-Adresse eines Songs: open.spotify.com/track/…",
                       className="text-muted d-block mb-2"),
            dbc.Row([
                dbc.Col(dbc.Input(id="ver-merge-source", placeholder="Song-ID"), md=5),
                dbc.Col(dbc.Input(id="ver-merge-target", placeholder="zählt zu Song-ID"), md=5),
                dbc.Col(dbc.Button("Zusammen zählen", id="ver-merge-manual", color="primary", className="w-100"),
                        md=2),
            ], className="g-2"),
        ]), className="mb-3"),
        html.Div("Deine Entscheidungen", className="fw-semibold mb-2"),
        html.Div(id="ver-overrides", children=overrides),
    ], className="pt-3")


def layout():
    # Status direkt beim Seitenaufbau rendern: ein Callback, der nur an ver-refresh hängt,
    # wird von Dash verworfen, wenn handle_action beim Rendern der Buttons kurz mitläuft
    status, overrides = _status_children()
    return dbc.Container([
        dcc.Store(id="ver-refresh", data=0),
        html.Div(id="ver-feedback", className="toast-area"),
        dbc.Card(dbc.CardBody(html.Div(id="ver-status", children=status)), className="mb-3"),
        dbc.Tabs([
            dbc.Tab(_groups_tab(), label="Songs", tab_id="groups"),
            dbc.Tab(_suggestions_tab(), label="Vorschläge", tab_id="suggestions"),
            dbc.Tab(_changes_tab(), label="Änderungen", tab_id="changes"),
            dbc.Tab(_manual_tab(overrides), label="Deine Entscheidungen", tab_id="manual"),
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


def _num(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def _sync_text(value: str) -> str:
    # Ältere Einträge wurden noch als "ok: ..." gespeichert
    if value and value.startswith("ok: "):
        return "fertig – " + value[4:]
    return value or "—"


def _status_children():
    s = catalog_status()
    kinds = s["kinds"]
    status = html.Div([
        html.Div([
            html.Span(f"{_num(s['groups'])} Songs gibt es in mehreren Versionen", className="fw-semibold me-3"),
            *[dbc.Badge(f"{_num(kinds.get(k, 0))} {KIND_LABELS[k]}", color=KIND_COLORS[k], className="me-1")
              for k in KIND_LABELS],
        ], className="mb-2"),
        html.Ul([
            html.Li([html.B("Hauptversion: "), "Unter ihr werden die Streams aller Versionen zusammengezählt."]),
            html.Li([html.B("Veraltet: "), "Spotify hat den Song durch eine neue Version ersetzt und spielt nur noch "
                     "die neue ab. Nur solche Songs lassen sich in Playlists austauschen."]),
            html.Li([html.B("Weiteres Release: "), "Dieselbe Aufnahme auf einer anderen Veröffentlichung, z. B. als "
                     "Single und auf dem Album. Beide bleiben, wie sie sind; nur die Streams werden zusammengezählt."]),
        ], className="small text-muted mb-2 ps-3"),
        html.Small(f"{_num(s['checked'] or 0)} von {_num(s['songs'])} Songs mit Spotify abgeglichen · "
                   f"{_num(s['relinked'] or 0)} veraltet · {_num(s['dead'] or 0)} nicht mehr auf Spotify",
                   className="text-muted d-block"),
        *[html.Small(f"{SYNC_LABELS.get(name, name)}: {_sync_text(value)} ({local_time(updated)})",
                     className="text-muted d-block") for name, (value, updated) in sorted(s["state"].items())],
    ])
    if not s["overrides"]:
        overrides = html.Div("Du hast noch nichts selbst festgelegt.", className="text-muted small")
    else:
        overrides = dbc.ListGroup([dbc.ListGroupItem(html.Div([
            html.Div([
                html.Span(o["song_name"] or o["song_id"]),
                html.Small(f" zählt zu {o['target_name'] or o['target_song_id']}" if o["target_song_id"]
                           else " wird immer getrennt gezählt", className="text-muted"),
            ]),
            dbc.Button("Rückgängig", id={"type": "ver-unoverride", "song": o["song_id"]}, size="sm",
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
    label = f"Seite {min(int(page or 0) + 1, pages)} von {pages} · {_num(result['total'])} Songs"
    if not result["groups"]:
        return empty_state("Nichts gefunden", "Probier einen anderen Suchbegriff oder Filter.",
                           icon="bi bi-layers"), label
    return [_group_card(g) for g in result["groups"]], label


@callback(
    Output("ver-sugg-page", "data"),
    Input("ver-sugg-prev", "n_clicks"),
    Input("ver-sugg-next", "n_clicks"),
    Input("ver-sugg-search", "value"),
    State("ver-sugg-page", "data"),
    prevent_initial_call=True
)
def change_suggestion_page(_prev, _next, _search, page):
    if ctx.triggered_id == "ver-sugg-prev":
        return max(0, (page or 0) - 1)
    if ctx.triggered_id == "ver-sugg-next":
        return (page or 0) + 1
    return 0


@callback(
    Output("ver-suggestions", "children"),
    Output("ver-sugg-page-label", "children"),
    Output("ver-sugg-all", "value"),
    Input("ver-sugg-page", "data"),
    Input("ver-refresh", "data"),
    State("ver-sugg-search", "value"),
    State("cache-version", "data"),
)
def update_suggestions(page, _refresh, search, cache_ver):
    items = suggestions((search or "").strip(), int(cache_ver or 0))
    pages = max(1, math.ceil(len(items) / SUGGESTION_PAGE_SIZE))
    page = min(int(page or 0), pages - 1)
    label = f"Seite {page + 1} von {pages} · {count(len(items), 'Vorschlag', 'Vorschläge')}"
    if not items:
        return empty_state("Keine Vorschläge", "Gerade gibt es nichts zu prüfen.", icon="bi bi-check2-all"), label, False
    shown = items[page * SUGGESTION_PAGE_SIZE:(page + 1) * SUGGESTION_PAGE_SIZE]
    return [_suggestion_card(s) for s in shown], label, False


@callback(
    Output({"type": "ver-sugg-check", "song": ALL, "target": ALL}, "value"),
    Input("ver-sugg-all", "value"),
    State({"type": "ver-sugg-check", "song": ALL, "target": ALL}, "value"),
    prevent_initial_call=True
)
def select_all_suggestions(select_all, current):
    return [bool(select_all)] * len(current)


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
        is_availability = df["field"] == "available"
        for col in ("old_value", "new_value"):
            df.loc[is_availability, col] = df.loc[is_availability, col].map(
                {"1": "verfügbar", "0": "nicht verfügbar"}).fillna(df.loc[is_availability, col])
        df["entity"] = df["entity"].map(ENTITY_LABELS).fillna(df["entity"])
        df["field"] = df["field"].map(FIELD_LABELS).fillna(df["field"])
        df["source"] = df["source"].map(SOURCE_LABELS).fillna(df["source"])
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
    Input("ver-sugg-merge-selected", "n_clicks"),
    Input("ver-sugg-dismiss-selected", "n_clicks"),
    State("ver-merge-source", "value"),
    State("ver-merge-target", "value"),
    State({"type": "ver-sugg-check", "song": ALL, "target": ALL}, "value"),
    State({"type": "ver-sugg-check", "song": ALL, "target": ALL}, "id"),
    State("ver-refresh", "data"),
    prevent_initial_call=True
)
def handle_action(_split, _merge, _dismiss, _unoverride, _manual, _merge_sel, _dismiss_sel, source, target,
                  checked, check_ids, refresh):
    # Neu gerenderte Buttons lösen den Callback mit n_clicks=None aus -> ignorieren
    if not ctx.triggered or not ctx.triggered[0]["value"]:
        return no_update, no_update, no_update
    trg = ctx.triggered_id
    if trg in ("ver-sugg-merge-selected", "ver-sugg-dismiss-selected"):
        pairs = [(cid["song"], cid["target"]) for cid, on in zip(check_ids or [], checked or []) if on]
        if not pairs:
            return dbc.Alert("Wähl zuerst mindestens einen Vorschlag aus.", color="info", duration=3000), \
                no_update, no_update
        if trg == "ver-sugg-merge-selected":
            n = merge_many(pairs)
            text = f"Erledigt – {count(n, 'Paar wird', 'Paare werden')} jetzt zusammen gezählt."
        else:
            n = dismiss_many(pairs)
            text = f"Alles klar, {count(n, 'Vorschlag taucht', 'Vorschläge tauchen')} nicht mehr auf."
        return dbc.Alert(text, color="success", duration=4000), (refresh or 0) + 1, bump_data_version()
    if trg == "ver-merge-manual":
        msg = merge_songs(source, target)
        text = "Erledigt – die beiden Songs werden jetzt zusammen gezählt." if msg == "ok" else msg
    elif trg["type"] == "ver-split":
        split_song(trg["song"])
        msg, text = "ok", "Erledigt – diese Version wird ab jetzt getrennt gezählt."
    elif trg["type"] == "ver-merge":
        msg = merge_songs(trg["song"], trg["target"])
        text = "Erledigt – die beiden Songs werden jetzt zusammen gezählt." if msg == "ok" else msg
    elif trg["type"] == "ver-dismiss":
        msg, text = dismiss_suggestion(trg["song"], trg["target"]), "Alles klar, der Vorschlag taucht nicht mehr auf."
    else:
        msg, text = remove_override(trg["song"]), "Rückgängig gemacht."
    if msg != "ok":
        return dbc.Alert(text, color="warning", duration=5000), no_update, no_update
    # Neue Datenversion -> alle gecachten Statistiken rechnen mit den neuen Gruppen
    return dbc.Alert(text, color="success", duration=4000), (refresh or 0) + 1, bump_data_version()
