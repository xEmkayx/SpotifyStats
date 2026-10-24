import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback, no_update

from frontend_new.components.charts import build_streams_timeline_figure, build_weekday_hour_figure
from frontend_new.components.empty_state import skeleton_graph
from frontend_new.components.filters import (
    build_filter_panel, date_range, quick_ranges, metric_toggle, fid, aid, mid, make_sidebar_layout
)
from frontend_new.components.page_callbacks import register_sidebar_toggle, register_quick_ranges
from frontend_new.services.dashboard import dashboard_kpis, daily_streams, weekday_hour_streams
from frontend_new.services.summary import format_duration_de

SCOPE = "dashboard"
dash.register_page(__name__, path="/dashboard", name="Dashboard", group="Analyse", order=20)


def _kpi(label: str, value: str, icon: str):
    return dbc.Col(dbc.Card(dbc.CardBody([
        html.Div([html.I(className=f"{icon} me-2"), label], className="text-muted small"),
        html.Div(value, className="h4 mb-0 mt-1"),
    ], className="py-2")), xs=6, md=4, xl=2, className="mb-3")


def layout():
    filters = build_filter_panel(
        scope=SCOPE,
        controls=[date_range(SCOPE, default_days=365), quick_ranges(SCOPE), metric_toggle(SCOPE)],
        with_apply=True,
        variant="plain"
    )
    right = [
        dcc.Loading(html.Div(id=f"{SCOPE}-kpis", children=skeleton_graph(height=90))),
        dbc.Card([
            dbc.CardHeader("Wie viel du hörst"),
            dbc.CardBody(dcc.Loading(html.Div(id=f"{SCOPE}-timeline", children=skeleton_graph(height=380))))
        ], className="mb-3"),
        dbc.Card([
            dbc.CardHeader("Wann du hörst"),
            dbc.CardBody(dcc.Loading(html.Div(id=f"{SCOPE}-weekhour", children=skeleton_graph(height=340))))
        ]),
    ]
    return make_sidebar_layout(scope=SCOPE, sidebar_children=filters, content_children=right, title="Filter")


register_quick_ranges(SCOPE)
register_sidebar_toggle(SCOPE)


@callback(
    Output(f"{SCOPE}-kpis", "children"),
    Output(f"{SCOPE}-weekhour", "children"),
    Input(aid(SCOPE), "n_clicks"),
    State(fid(SCOPE, "date"), "start_date"),
    State(fid(SCOPE, "date"), "end_date"),
    State("theme", "data"),
    State("cache-version", "data"),
)
def update_kpis(_, start_date, end_date, theme, cache_ver):
    if not start_date or not end_date:
        return no_update, no_update
    k = dashboard_kpis(start_date, end_date, int(cache_ver or 0))
    per_day = round(k["streams"] / k["active_days"], 1) if k["active_days"] else 0
    kpis = dbc.Row([
        _kpi("Streams", f"{k['streams']:,}".replace(",", "."), "bi bi-play-circle"),
        _kpi("Hörzeit", f"{round(k['seconds_total'] / 3600):,} h".replace(",", "."), "bi bi-clock"),
        _kpi("Songs", f"{k['songs']:,}".replace(",", "."), "bi bi-music-note"),
        _kpi("Artists", f"{k['artists']:,}".replace(",", "."), "bi bi-person"),
        _kpi("Alben", f"{k['albums']:,}".replace(",", "."), "bi bi-disc"),
        _kpi("Streams pro Hörtag", f"{per_day}".replace(".", ","), "bi bi-calendar-check"),
    ], className="g-3")
    hint = html.Div(f"Du hast an {k['active_days']} Tagen Musik gehört, insgesamt etwa "
                    f"{format_duration_de(k['seconds_total'])}.", className="text-muted small mb-3")
    wh = weekday_hour_streams(start_date, end_date, int(cache_ver or 0))
    fig_wh = build_weekday_hour_figure(wh, dark=(theme == "dark"))
    return [kpis, hint], dcc.Graph(figure=fig_wh, config={"displayModeBar": False})


@callback(
    Output(f"{SCOPE}-timeline", "children"),
    Input(aid(SCOPE), "n_clicks"),
    Input(mid(SCOPE), "value"),
    State(fid(SCOPE, "date"), "start_date"),
    State(fid(SCOPE, "date"), "end_date"),
    State("theme", "data"),
    State("cache-version", "data"),
)
def update_timeline(_, metric, start_date, end_date, theme, cache_ver):
    if not start_date or not end_date:
        return no_update
    df = daily_streams(start_date, end_date, int(cache_ver or 0))
    fig = build_streams_timeline_figure(df, (metric or "plays").lower(), dark=(theme == "dark"))
    return dcc.Graph(figure=fig, config={"displayModeBar": True})
