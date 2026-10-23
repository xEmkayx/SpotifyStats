import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback, no_update

from frontend_new.components.charts import build_sunburst_figure, SUNBURST_PATHS
from frontend_new.components.empty_state import skeleton_graph
from frontend_new.components.filters import (
    build_filter_panel, date_range, quick_ranges, topn_slider, metric_toggle, fid, aid, mid, make_sidebar_layout,
    form_group
)
from frontend_new.components.page_callbacks import register_sidebar_toggle, register_quick_ranges
from frontend_new.services.top_songs import cached_top_songs

SCOPE = "sunburst"
dash.register_page(__name__, path="/sunburst", name="Sunburst", group="Charts", order=14)


def hierarchy_select(scope: str):
    return form_group("Hierarchie", dbc.Select(
        id=fid(scope, "hierarchy"),
        options=[{"label": label, "value": key} for key, (_, label) in SUNBURST_PATHS.items()],
        value="artist-album-song",
    ))


def layout():
    filters = build_filter_panel(
        scope=SCOPE,
        controls=[
            date_range(SCOPE, default_days=365),
            quick_ranges(SCOPE),
            hierarchy_select(SCOPE),
            topn_slider(SCOPE, label="Anzahl Songs", default=300, minv=50, maxv=1000, step=50),
        ],
        with_apply=True,
        variant="plain"
    )
    right = [
        dbc.Card([
            dbc.CardHeader(dbc.Row([
                dbc.Col(html.Div("Sunburst"), align="center"),
                dbc.Col(metric_toggle(SCOPE), width="auto", align="center", className="ms-auto"),
            ], className="g-2")),
            dbc.CardBody(dcc.Loading(children=html.Div(id=f"{SCOPE}-visual", children=skeleton_graph(height=700))))
        ])
    ]
    return make_sidebar_layout(scope=SCOPE, sidebar_children=filters, content_children=right, title="Filter")


register_quick_ranges(SCOPE)
register_sidebar_toggle(SCOPE)


@callback(
    Output(f"{SCOPE}-visual", "children"),
    Input(aid(SCOPE), "n_clicks"),
    Input(mid(SCOPE), "value"),
    State(fid(SCOPE, "date"), "start_date"),
    State(fid(SCOPE, "date"), "end_date"),
    State(fid(SCOPE, "hierarchy"), "value"),
    State(fid(SCOPE, "top_n"), "value"),
    State("theme", "data"),
    State("cache-version", "data"),
)
def update_sunburst(_, metric, start_date, end_date, hierarchy, top_n, theme, cache_ver):
    if not start_date or not end_date:
        return no_update
    metric = (metric or "plays").lower()
    df = cached_top_songs(f"{start_date} 00:00", f"{end_date} 23:59", int(top_n or 300), metric,
                          int(cache_ver or 0))
    fig = build_sunburst_figure(df, hierarchy or "artist-album-song", metric, dark=(theme == "dark"))
    return dcc.Graph(figure=fig, config={"displayModeBar": True})
