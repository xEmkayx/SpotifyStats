from datetime import timedelta, date

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback, no_update, ALL, ctx

from frontend_new.components.charts import build_top_songs_figure
from frontend_new.components.empty_state import skeleton_graph
from frontend_new.components.filters import date_range, topn_slider, build_filter_panel, quick_ranges, metric_toggle, \
    fid, qid, aid, mid, make_sidebar_layout, sidebar_id, siid, stid
from frontend_new.components.playlist import playlist_modal, playlist_status, playlist_button, pmodal, pbtn, pconfirm, \
    pstatus, pname, ppublic
from frontend_new.components.summaries import listening_time_summary, sid
from frontend_new.services.spotify_playlist import create_playlist_from_current_filters
from frontend_new.services.summary import cached_total_listening_seconds, format_duration_de
from frontend_new.services.top_songs import cached_top_songs

SCOPE = "top-songs"
dash.register_page(__name__, path="/top-songs", name="Top Songs")


def layout():
    filters = build_filter_panel(
        scope=SCOPE,
        controls=[
            date_range(SCOPE),
            quick_ranges(SCOPE),
            topn_slider(SCOPE, default=30)
        ],
        with_apply=True,
        variant="plain"  # wichtig für die Sidebar
    )
    right = [
        listening_time_summary(SCOPE),
        playlist_modal(SCOPE),  # Modal bereitstellen
        playlist_status(SCOPE),  # Platz für Status/Alerts
        dbc.Card([
            dbc.CardHeader(
                dbc.Row([
                    dbc.Col(html.Div("Top Songs"), align="center"),
                    dbc.Col(playlist_button(SCOPE), width="auto", align="center"),
                    dbc.Col(metric_toggle(SCOPE), width="auto", align="center", className="ms-auto")
                ], className="g-2")
            ),
            dbc.CardBody(
                dcc.Loading(
                    id="ts-loading",
                    type="default",
                    children=html.Div(id="ts-visual", children=skeleton_graph())  # Initialer Placeholder
                )
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
    Output("ts-visual", "children"),     # <-- children statt figure
    Input(aid(SCOPE), "n_clicks"),  # Apply-Button
    Input(mid(SCOPE), "value"),  # Metric-Toggle ("plays" | "minutes")
    State(fid(SCOPE, "date"), "start_date"),
    State(fid(SCOPE, "date"), "end_date"),
    State(fid(SCOPE, "top_n"), "value"),
    State("theme", "data"),  # "dark" | "light"
    State("cache-version", "data"),
    prevent_initial_call=True
)
def update_top_songs(n_apply, metric, start_date, end_date, top_n, theme, cache_ver):
    if not start_date or not end_date:
        return no_update

    start_dt = f"{start_date} 00:00"
    end_dt = f"{end_date} 23:59"
    metric = (metric or "plays").lower()

    df = cached_top_songs(
        start_dt,
        end_dt,
        int(top_n or 30),
        metric,
        int(cache_ver or 0)
    )

    dark = (theme == "dark")
    fig = build_top_songs_figure(df, metric, int(top_n or 30), dark)
    return dcc.Graph(id="ts-graph", figure=fig, config={"displayModeBar": True})


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


@callback(
Output(pmodal(SCOPE), "is_open"),
Input(pbtn(SCOPE), "n_clicks"),
Input({"type":"modal-cancel","scope":SCOPE}, "n_clicks"),
Input(pconfirm(SCOPE), "n_clicks"),
State(pmodal(SCOPE), "is_open"),
)
def toggle_playlist_modal(n_open, n_cancel, n_confirm, is_open):
    if any([n_open, n_cancel, n_confirm]):
        return not bool(is_open)
    return is_open


@callback(
Output(pstatus(SCOPE), "children"),
Input(pconfirm(SCOPE), "n_clicks"),
State(pname(SCOPE), "value"),
State(ppublic(SCOPE), "value"),
State(fid(SCOPE, "date"), "start_date"),
State(fid(SCOPE, "date"), "end_date"),
State(fid(SCOPE, "top_n"), "value"),
State(mid(SCOPE), "value"),
State("cache-version", "data"),
prevent_initial_call=True
)
def on_create_playlist(n, name, public, start_date, end_date, top_n, metric, cache_ver):
    if not n:
        return no_update
    if not start_date or not end_date:
        return dbc.Alert("Bitte zuerst einen gültigen Zeitraum wählen.", color="warning", duration=4000)

    ok, msg, url = create_playlist_from_current_filters(
        start_date=start_date,
        end_date=end_date,
        metric=(metric or "plays"),
        top_n=int(top_n or 30),
        cache_version=int(cache_ver or 0),
        playlist_name=name,
        public=bool(public)
    )
    if ok:
        link = html.A("In Spotify öffnen", href=url, target="_blank", className="ms-2") if url else ""
        return dbc.Alert([msg, " ", link], color="success", duration=6000, is_open=True)
    else:
        return dbc.Alert(msg, color="danger", duration=8000, is_open=True)
