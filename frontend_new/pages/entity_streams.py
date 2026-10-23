from datetime import date

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback, no_update

from frontend_new.components.charts import build_entity_songs_figure
from frontend_new.components.empty_state import empty_state
from frontend_new.components.filters import (
    build_filter_panel, date_range, quick_ranges, topn_slider, metric_toggle, text_input, fid, aid, mid,
    make_sidebar_layout, form_group
)
from frontend_new.components.page_callbacks import register_sidebar_toggle, register_quick_ranges
from frontend_new.services.entity_streams import entity_song_streams

SCOPE = "entity-streams"
dash.register_page(__name__, path="/streams-search", name="Streams-Suche", group="Analyse", order=22)

CATEGORY_LABELS = {"artist": "Artist", "album": "Album", "song": "Song"}


def _segmented(scope: str, name: str, label: str, options: list, value: str):
    return form_group(label, html.Div(
        dbc.RadioItems(
            id=fid(scope, name),
            className="btn-group segmented-group",
            inputClassName="btn-check",
            labelClassName="btn",
            labelCheckedClassName="active",
            options=options,
            value=value,
        ),
        className="segmented-toggle compact"
    ))


def layout():
    filters = build_filter_panel(
        scope=SCOPE,
        controls=[
            _segmented(SCOPE, "category", "Suchen nach",
                       [{"label": v, "value": k} for k, v in CATEGORY_LABELS.items()], "artist"),
            _segmented(SCOPE, "match", "Vergleich über",
                       [{"label": "Name", "value": "name"}, {"label": "ID", "value": "id"}], "name"),
            text_input(SCOPE, "query", "Suchbegriff", placeholder="z. B. Daft Punk"),
            # Standard: gesamte Historie, wie in den alten Single-Seiten
            date_range(SCOPE, default_days=(date.today() - date(2015, 1, 1)).days),
            quick_ranges(SCOPE),
            topn_slider(SCOPE, label="Max. Songs", default=50, minv=10, maxv=200, step=10),
        ],
        with_apply=True,
        variant="plain"
    )
    right = [
        dbc.Card([
            dbc.CardHeader(dbc.Row([
                dbc.Col(html.Div("Streams pro Song"), align="center"),
                dbc.Col(metric_toggle(SCOPE), width="auto", align="center", className="ms-auto"),
            ], className="g-2")),
            dbc.CardBody(dcc.Loading(children=html.Div(
                id=f"{SCOPE}-visual",
                children=empty_state("Noch keine Suche", "Artist, Album oder Songtitel eingeben und anwenden.",
                                     icon="bi bi-search")
            )))
        ])
    ]
    return make_sidebar_layout(scope=SCOPE, sidebar_children=filters, content_children=right, title="Filter")


register_quick_ranges(SCOPE)
register_sidebar_toggle(SCOPE)


@callback(
    Output(f"{SCOPE}-visual", "children"),
    Input(aid(SCOPE), "n_clicks"),
    Input(mid(SCOPE), "value"),
    State(fid(SCOPE, "category"), "value"),
    State(fid(SCOPE, "match"), "value"),
    State(fid(SCOPE, "query"), "value"),
    State(fid(SCOPE, "date"), "start_date"),
    State(fid(SCOPE, "date"), "end_date"),
    State(fid(SCOPE, "top_n"), "value"),
    State("theme", "data"),
    State("cache-version", "data"),
    prevent_initial_call=True
)
def update_visual(_, metric, category, match, query, start_date, end_date, top_n, theme, cache_ver):
    query = (query or "").strip()
    if not query:
        return empty_state("Kein Suchbegriff", "Bitte einen Suchbegriff eingeben.", icon="bi bi-search")
    if not start_date or not end_date:
        return no_update
    metric = (metric or "plays").lower()
    df = entity_song_streams(category, match, query, start_date, end_date, int(top_n or 50), metric,
                             int(cache_ver or 0))
    if df.empty:
        return empty_state("Keine Treffer", "Suchbegriff oder Zeitraum anpassen.", icon="bi bi-funnel")
    title = f'{CATEGORY_LABELS.get(category, "")} "{query}": {len(df)} Songs, {int(df["plays"].sum())} Streams'
    fig = build_entity_songs_figure(df, metric, title, dark=(theme == "dark"))
    return dcc.Graph(figure=fig, config={"displayModeBar": True})
