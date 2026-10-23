import math

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback, dash_table, no_update

from frontend_new.components.filters import (
    build_filter_panel, date_range, quick_ranges, text_input, fid, aid, make_sidebar_layout
)
from frontend_new.components.page_callbacks import register_sidebar_toggle, register_quick_ranges
from frontend_new.services.history import history_page, history_totals
from frontend_new.services.summary import format_duration_de

SCOPE = "history"
PAGE_SIZE = 50
dash.register_page(__name__, path="/history", name="Hörhistorie", group="Analyse", order=21)

COLUMNS = [
    {"name": "Gespielt am", "id": "played_at"},
    {"name": "Song", "id": "song_name"},
    {"name": "Artists", "id": "artists"},
    {"name": "Album", "id": "album_name"},
    {"name": "Länge", "id": "song_length"},
]


def layout():
    filters = build_filter_panel(
        scope=SCOPE,
        controls=[
            date_range(SCOPE, default_days=30),
            quick_ranges(SCOPE),
            text_input(SCOPE, "search", "Suche (Song, Artist, Album)", placeholder="optional"),
        ],
        with_apply=True,
        variant="plain"
    )
    right = [
        dbc.Card([
            dbc.CardHeader("Überblick"),
            dbc.CardBody(html.Div(id=f"{SCOPE}-totals", className="fw-semibold"), className="py-2")
        ], className="mb-3"),
        dbc.Card([
            dbc.CardHeader("Streams"),
            dbc.CardBody(dcc.Loading(dash_table.DataTable(
                id=f"{SCOPE}-table",
                columns=COLUMNS,
                data=[],
                page_current=0,
                page_size=PAGE_SIZE,
                page_count=1,
                page_action="custom",  # Paginierung serverseitig per LIMIT/OFFSET
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left", "padding": "6px", "backgroundColor": "transparent",
                            "color": "inherit", "border": "1px solid rgba(255,255,255,.08)",
                            "maxWidth": "320px", "overflow": "hidden", "textOverflow": "ellipsis"},
                style_header={"fontWeight": "600", "backgroundColor": "rgba(255,255,255,.04)"},
            )))
        ])
    ]
    return make_sidebar_layout(scope=SCOPE, sidebar_children=filters, content_children=right, title="Filter")


register_quick_ranges(SCOPE)
register_sidebar_toggle(SCOPE)


@callback(
    Output(f"{SCOPE}-table", "page_current"),
    Input(aid(SCOPE), "n_clicks"),
    prevent_initial_call=True
)
def reset_page(_):
    # Neue Filter -> zurück auf Seite 1
    return 0


@callback(
    Output(f"{SCOPE}-totals", "children"),
    Output(f"{SCOPE}-table", "page_count"),
    Input(aid(SCOPE), "n_clicks"),
    State(fid(SCOPE, "date"), "start_date"),
    State(fid(SCOPE, "date"), "end_date"),
    State(fid(SCOPE, "search"), "value"),
    State("cache-version", "data"),
)
def update_totals(_, start_date, end_date, search, cache_ver):
    if not start_date or not end_date:
        return "Bitte Zeitraum wählen.", 1
    t = history_totals(start_date, end_date, search or "", int(cache_ver or 0))
    text = f"{t['streams']} Streams • (Ungefähre) Hörzeit: {format_duration_de(t['seconds_total'])}"
    return text, max(1, math.ceil(t["streams"] / PAGE_SIZE))


@callback(
    Output(f"{SCOPE}-table", "data"),
    Input(aid(SCOPE), "n_clicks"),
    Input(f"{SCOPE}-table", "page_current"),
    State(fid(SCOPE, "date"), "start_date"),
    State(fid(SCOPE, "date"), "end_date"),
    State(fid(SCOPE, "search"), "value"),
    State("cache-version", "data"),
)
def update_table(_, page, start_date, end_date, search, cache_ver):
    if not start_date or not end_date:
        return no_update
    df = history_page(start_date, end_date, search or "", int(page or 0), PAGE_SIZE, int(cache_ver or 0))
    return df.to_dict("records")
