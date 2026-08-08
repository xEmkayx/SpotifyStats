from datetime import timedelta, date
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback, no_update, ALL, ctx

from frontend_new.components.empty_state import skeleton_graph
from frontend_new.components.filters import date_range, topn_slider, build_filter_panel, quick_ranges, metric_toggle, \
    fid, qid, aid, mid, make_sidebar_layout, sidebar_id, siid, stid
from frontend_new.components.summaries import listening_time_summary, sid
from frontend_new.components.charts import build_top_artists_figure
from frontend_new.services.summary import cached_total_listening_seconds, format_duration_de
from frontend_new.services.top_artists import cached_top_artists

SCOPE = "top-artists"
dash.register_page(__name__, path="/top-artists", name="Top Artists")

def layout():
    filters = build_filter_panel(
        scope=SCOPE,
        controls=[date_range(SCOPE), quick_ranges(SCOPE), topn_slider(SCOPE, default=30)],
        with_apply=True,
        variant="plain"
    )
    right = [
        listening_time_summary(SCOPE),
        dbc.Card([
            dbc.CardHeader(
                dbc.Row([
                    dbc.Col(html.Div("Top Artists"), align="center"),
                    dbc.Col(metric_toggle(SCOPE), width="auto", align="center", className="ms-auto"),
                ], className="g-2")
            ),
            dbc.CardBody(
                dcc.Loading(id="ta-loading", type="default",
                            children=html.Div(id="ta-visual", children=skeleton_graph()))
            ),
        ])
    ]
    return make_sidebar_layout(scope=SCOPE, sidebar_children=filters, content_children=right, title="Filter")

@callback(
    Output(fid(SCOPE, "date"), "start_date"),
    Output(fid(SCOPE, "date"), "end_date"),
    Input(qid(SCOPE, ALL), "n_clicks"),
    prevent_initial_call=True
)
def set_quick_range(_):
    trg = ctx.triggered_id
    if not isinstance(trg, dict):
        raise dash.exceptions.PreventUpdate
    today = date.today()
    name = trg.get("name")
    start = today - timedelta(days=7 if name=="1w" else 30 if name=="1m" else 365)
    return start, today

@callback(
    Output("ta-visual", "children"),
    Input(aid(SCOPE), "n_clicks"),
    Input(mid(SCOPE), "value"),
    State(fid(SCOPE, "date"), "start_date"),
    State(fid(SCOPE, "date"), "end_date"),
    State(fid(SCOPE, "top_n"), "value"),
    State("theme", "data"),
    State("cache-version", "data"),
    prevent_initial_call=True
)
def update_top_artists(n_apply, metric, start_date, end_date, top_n, theme, cache_ver):
    if not start_date or not end_date:
        return no_update
    start_dt = f"{start_date} 00:00"
    end_dt = f"{end_date} 23:59"
    metric = (metric or "plays").lower()

    df = cached_top_artists(start_dt, end_dt, int(top_n or 30), metric, int(cache_ver or 0))

    dark = (theme == "dark")
    fig = build_top_artists_figure(df, metric, int(top_n or 30), dark)
    return dcc.Graph(id="ta-graph", figure=fig, config={"displayModeBar": True})

@callback(
    Output(sid(SCOPE, "listening_time"), "children"),
    Input(aid(SCOPE), "n_clicks"),
    State(fid(SCOPE, "date"), "start_date"),
    State(fid(SCOPE, "date"), "end_date"),
    State("cache-version", "data"),
    prevent_initial_call=True
)
def update_listening_time(n_apply, start_date, end_date, cache_ver):
    if not start_date or not end_date:
        return no_update
    start_dt = f"{start_date} 00:00"
    end_dt = f"{end_date} 23:59"
    seconds = cached_total_listening_seconds(start_dt, end_dt, int(cache_ver or 0))
    pretty = format_duration_de(seconds)
    return f"(Ungefähre) Gesamte Hörzeit: {pretty}"

@callback(
    Output(sidebar_id(SCOPE), "className"),
    Output(siid(SCOPE), "className"),
    Input(stid(SCOPE), "n_clicks"),
    State(sidebar_id(SCOPE), "className"),
)
def toggle_sidebar(n, cls):
    if not n:
        return cls or "sidebar", "bi bi-chevron-left"
    cls = cls or "sidebar"
    collapsed = "collapsed" in cls
    new_cls = "sidebar" if collapsed else "sidebar collapsed"
    icon = "bi bi-chevron-left" if collapsed else "bi bi-chevron-right"
    return new_cls, icon
