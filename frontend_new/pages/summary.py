from datetime import date, timedelta

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback, no_update, ctx

from frontend_new.components.cards import cards_grid, map_song_items, map_artist_items, map_album_items
from frontend_new.components.empty_state import empty_state, skeleton_graph
from frontend_new.components.filters import (
    build_filter_panel, date_range, quick_ranges, topn_slider, metric_toggle, fid, qid, aid, mid, catid, sidebar_id,
    stid, siid, make_sidebar_layout
)
from frontend_new.components.summaries import listening_time_summary, sid as summary_id
from frontend_new.services.spotify_images import track_images, artist_images, album_images
from frontend_new.services.summary import cached_total_listening_seconds, format_duration_de
from frontend_new.services.summary_data import top_songs_data, top_artists_data, top_albums_data

SCOPE = "summary"
dash.register_page(__name__, path="/summary", name="Summary")


def layout():
    filters = build_filter_panel(
    scope=SCOPE,
    controls=[
    date_range(SCOPE),
    quick_ranges(SCOPE),
    topn_slider(SCOPE, default=24),
    metric_toggle(SCOPE),
    ],
    with_apply=True,
    variant="plain"
    )

    category_tabs = dbc.Tabs(
        id=catid(SCOPE),
        active_tab="songs",
        children=[
            dbc.Tab(label="Songs", tab_id="songs"),
            dbc.Tab(label="Artists", tab_id="artists"),
            dbc.Tab(label="Alben", tab_id="albums"),
        ],
        class_name="nav-tabs card-header-tabs tabs-minimal",  # nav-fill raus
        persistence=True
    )

    right = [
        listening_time_summary(SCOPE),
        dbc.Card([
            # dbc.CardHeader(
            #     dbc.Row([
            #         # dbc.Col(html.Span("Übersicht"), width="auto"),
            #         dbc.Col(category_tabs),
            #     ], align="center", className="g-2"),
            #     className="py-2"
            # ),
            dbc.CardHeader(
                html.Div(category_tabs, className="d-flex justify-content-center"),
                className="py-3 tabs-header"  # mehr Luft + Hook für CSS
            ),
            dbc.CardBody(
                dcc.Loading(children=html.Div(id=f"{SCOPE}-visual", children=skeleton_graph(height=420)))
            )
        ])
    ]
    return make_sidebar_layout(scope=SCOPE, sidebar_children=filters, content_children=right, title="Filter")


# Quick-Range
@callback(
Output(fid(SCOPE, "date"), "start_date"),
Output(fid(SCOPE, "date"), "end_date"),
Input(qid(SCOPE, "1w"), "n_clicks"),
Input(qid(SCOPE, "1m"), "n_clicks"),
Input(qid(SCOPE, "1y"), "n_clicks"),
)
def set_quick_range(n1, n2, n3):
    if not ctx.triggered_id: return no_update, no_update
    today = date.today()
    name = ctx.triggered_id["name"]
    start = today - timedelta(days=7 if name=="1w" else 30 if name=="1m" else 365)
    return start, today


# Sidebar-Toggle
@callback(
Output(sidebar_id(SCOPE), "className"),
Output(siid(SCOPE), "className"),
Input(stid(SCOPE), "n_clicks"),
State(sidebar_id(SCOPE), "className"),
)
def toggle_sidebar(n, cls):
    if not n: return cls or "sidebar", "bi bi-chevron-left"
    cls = cls or "sidebar"
    collapsed = "collapsed" in cls
    return ("sidebar" if collapsed else "sidebar collapsed",
    "bi bi-chevron-left" if collapsed else "bi bi-chevron-right")


# Hörzeit
@callback(
Output(summary_id(SCOPE, "listening_time"), "children"),
Input(aid(SCOPE), "n_clicks"),
State(fid(SCOPE, "date"), "start_date"),
State(fid(SCOPE, "date"), "end_date"),
State("cache-version", "data"),
)
def update_listening_time(_, start_date, end_date, cache_ver):
    if not start_date or not end_date: return no_update
    secs = cached_total_listening_seconds(f"{start_date} 00:00", f"{end_date} 23:59", int(cache_ver or 0))
    return f"(Ungefähre) Gesamte Hörzeit: {format_duration_de(secs)}"


# Karten aktualisieren
@callback(
Output(f"{SCOPE}-visual", "children"),
Input(aid(SCOPE), "n_clicks"),                 # nur auf Anwenden reagieren
State(catid(SCOPE), "active_tab"),             # Tabs als State => “lazy”
State(mid(SCOPE), "value"),
State(fid(SCOPE, "date"), "start_date"),
State(fid(SCOPE, "date"), "end_date"),
State(fid(SCOPE, "top_n"), "value"),
State("cache-version", "data"),
)
def update_cards(n_apply, category, metric, start_date, end_date, top_n, cache_ver):
    if not start_date or not end_date:
        return empty_state("Keine Daten", "Bitte Zeitraum wählen.")
    start_dt = f"{start_date} 00:00"
    end_dt   = f"{end_date} 23:59"
    metric = (metric or "plays").lower()
    top_n = int(top_n or 24)

    try:
        if category == "artists":
            df = top_artists_data(start_dt, end_dt, top_n, metric, int(cache_ver or 0))
            if df.empty: return empty_state("Keine Artists im Zeitraum", "Filter anpassen.", "bi bi-person")
            # Bilder (Batch)
            img_map = artist_images(tuple(df["artist_id"].tolist()))
            df["image_url"] = df["artist_id"].map(img_map).fillna("")
            items = map_artist_items(df)
            return cards_grid(items, "artists")

        elif category == "albums":
            df = top_albums_data(start_dt, end_dt, top_n, metric, int(cache_ver or 0))
            if df.empty: return empty_state("Keine Alben im Zeitraum", "Filter anpassen.", "bi bi-disc")
            img_map = album_images(tuple(df["album_id"].tolist()))
            df["image_url"] = df["album_id"].map(img_map).fillna("")
            items = map_album_items(df)
            return cards_grid(items, "albums")

        else:  # songs
            df = top_songs_data(start_dt, end_dt, top_n, metric, int(cache_ver or 0))
            if df.empty: return empty_state("Keine Songs im Zeitraum", "Filter anpassen.", "bi bi-music-note")
            img_map = track_images(tuple(df["song_id"].tolist()))
            df["image_url"] = df["song_id"].map(img_map).fillna("")
            items = map_song_items(df)
            return cards_grid(items, "songs")

    except Exception as e:
        return empty_state("Fehler beim Laden", str(e), "bi bi-exclamation-triangle")
