from datetime import date

import dash
import dash_bootstrap_components as dbc
from dash import dcc, Input, Output, State, callback, no_update, html

from frontend_new.components.charts import (
    build_song_heatmap_figure,
    build_song_lifecycle_figure,
    build_listening_clock_figure,
    build_interarrival_hist_figure,
)
from frontend_new.components.empty_state import skeleton_graph
from frontend_new.components.filters import build_filter_panel, dropdown, sidebar_id, siid, stid, \
    fid, aid, text_input, make_sidebar_layout, date_range
from frontend_new.services.song_heatmap import cached_daily_song_counts
from frontend_new.services.song_search import search_songs, get_song_option_by_id
from frontend_new.services.song_dynamics import (
    song_overview, song_weekly_counts, song_interarrival, song_clock
)

SCOPE = "song-details"
dash.register_page(__name__, path="/song-details", name="Song Details", group="Analyse", order=23)


def _year_options(n=6):
    this = date.today().year
    return [{"label": str(y), "value": y} for y in range(this, this - n, -1)]


def layout():
    filters = build_filter_panel(
        scope=SCOPE,
        controls=[
            dropdown(SCOPE, "song", "Song", options=[], multi=False,
                     placeholder="Song oder Artist eintippen"),
            text_input(SCOPE, "song_id", "…oder Song-ID", placeholder="z. B. 4uLU6hMCjMI75M1A2tKUQC"),
            date_range(SCOPE, "Zeitraum", default_days=365),
            dropdown(SCOPE, "year", "Jahr für den Kalender", options=_year_options(), multi=False, placeholder="Jahr wählen"),
        ],
        with_apply=True,
        variant="plain",
    )
    right = [
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Überblick"),
                dbc.CardBody(html.Div(id="songd-overview", children=skeleton_graph()))
            ]), md=12)
        ], className="mb-3"),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Verlauf"),
                dbc.CardBody(dcc.Loading(type="default", children=html.Div(id="songd-lifecycle", children=skeleton_graph())))
            ]), md=6),
            dbc.Col(dbc.Card([
                dbc.CardHeader("Uhrzeit und Abstände"),
                dbc.CardBody(dcc.Loading(type="default", children=html.Div([
                    html.Div(id="songd-clock", children=skeleton_graph()),
                    html.Hr(),
                    html.Div(id="songd-ia", children=skeleton_graph())
                ])))
            ]), md=6),
        ], className="mb-3"),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("An welchen Tagen"),
                dbc.CardBody(dcc.Loading(type="default", children=html.Div(id="songd-hm", children=skeleton_graph())))
            ]), md=12)
        ])
    ]
    return make_sidebar_layout(scope=SCOPE, sidebar_children=filters, content_children=right, title="Filter")


def make_kpi_item(scope: str, key: str, label: str, value: str, help_text: str):
    icon_id = f"{scope}-kpi-{key}-info"
    item = dbc.ListGroupItem(
        [
            html.Div(
                [
                    html.Span(label, className="me-2"),
                    html.I(id=icon_id, className="bi bi-info-circle text-muted", style={"cursor": "help"}),
                ],
                className="d-flex align-items-center",
            ),
            html.Span(value, className="ms-auto text-muted"),
        ],
        className="d-flex justify-content-between align-items-center",
    )
    tip = dbc.Tooltip(help_text, target=icon_id, placement="right", autohide=True, delay={"show": 250, "hide": 100})
    return item, tip


@callback(
    Output(fid(SCOPE, "song"), "value"),
    Output(fid(SCOPE, "song"), "options"),
    Input(fid(SCOPE, "song"), "search_value"),
    Input(fid(SCOPE, "song_id"), "value"),
    State(fid(SCOPE, "song"), "options"),
    prevent_initial_call=True
)
def update_song_selector(search_value, song_id, options):
    # identisch zur anderen Seite
    prop = dash.ctx.triggered[0]["prop_id"].split(".")[-1] if dash.ctx.triggered else None

    if prop == "search_value":
        q = (search_value or "").strip()
        if len(q) < 2:
            return no_update, no_update
        return no_update, search_songs(q, limit=50)

    if not song_id:
        return no_update, no_update
    opt = get_song_option_by_id(str(song_id).strip())
    if not opt:
        return no_update, options or []
    options = options or []
    if not any(o.get("value") == opt["value"] for o in options):
        options = [opt] + options
    return opt["value"], options


@callback(
    Output("songd-overview", "children"),
    Output("songd-lifecycle", "children"),
    Output("songd-clock", "children"),
    Output("songd-ia", "children"),
    Output("songd-hm", "children"),
    Input(aid(SCOPE), "n_clicks"),
    State(fid(SCOPE, "song"), "value"),
    State(fid(SCOPE, "song_id"), "value"),
    State(fid(SCOPE, "date"), "start_date"),
    State(fid(SCOPE, "date"), "end_date"),
    State(fid(SCOPE, "year"), "value"),
    State("theme", "data"),
    State("cache-version", "data"),
    prevent_initial_call=True
)
def update_all(n, song_id_dropdown, song_id_text, start_date, end_date, year, theme, cache_ver):
    chosen_id = (song_id_dropdown or song_id_text or "").strip()
    if not chosen_id:
        msg = dbc.Alert("Wähl links einen Song aus.", color="info")
        return msg, skeleton_graph(), skeleton_graph(), skeleton_graph(), skeleton_graph()

    # Overview
    ov = song_overview(chosen_id, start_date, end_date, int(cache_ver or 0))
    if not ov.get("exists"):
        msg = dbc.Alert("Diesen Song gibt es hier nicht.", color="warning")
        return msg, skeleton_graph(), skeleton_graph(), skeleton_graph(), skeleton_graph()

    dark = (theme == "dark")

    # Card links: Bild + Grundwerte, rechts: KPIs
    meta = ov["meta"]
    minutes = round((ov["seconds_total"] or 0) / 60.0, 1)
    img_url = meta.get("image_url") or ""
    if img_url:
        img_el = html.Img(
            src=img_url,
            alt="",
            style={"width": "120px", "height": "120px", "objectFit": "cover", "borderRadius": "8px"}
        )
    else:
        # simpler Placeholder mit Icon
        img_el = html.Div(
            html.I(className="bi bi-music-note-beamed", style={"fontSize": "48px", "color": "#888"}),
            style={
                "width": "120px", "height": "120px", "borderRadius": "8px",
                "background": "rgba(0,0,0,0.05)", "display": "flex",
                "alignItems": "center", "justifyContent": "center"
            }
        )

    card_left = html.Div([img_el], className="me-3")
    title = html.Div([
        html.Div(meta.get("song_name", ""), className="h5 mb-1"),
        html.Small(meta.get("artists", ""), className="text-muted d-block"),
        html.Small(meta.get("album_name", "") or "", className="text-muted d-block"),
        html.Small(f"{ov['total_plays']} Streams · {minutes} Minuten", className="text-muted d-block mt-2"),
        html.Small(html.A(f"Gibt es in {ov['versions']} Versionen – alle zusammengezählt", href="/versions"),
                   className="d-block") if ov.get("versions", 1) > 1 else None,
        html.A("In Spotify öffnen", href=f"https://open.spotify.com/track/{meta.get('song_id')}", target="_blank", className="mt-2 d-inline-block")
    ])
    kpis = [
        ("Erstes Play", ov["first_play"][:10] if ov.get("first_play") else "—"),
        ("Letztes Play", ov["last_play"][:10] if ov.get("last_play") else "—"),
        ("Tage mit Plays", f"{ov['unique_days']}"),
        ("Längste Streak", f"{ov['longest_streak_days']} Tage"),
        ("Median Gap", f"{ov['median_gap_days']} d" if ov.get("median_gap_days") is not None else "—"),
        ("Ø Gap", f"{ov['mean_gap_days']} d" if ov.get("mean_gap_days") is not None else "—"),
        ("Aktuelle Pause", f"{ov['current_silence_days']} d" if ov.get("current_silence_days") is not None else "—"),
        ("Tage bis 50%", f"{ov['days_to_50pct']} d" if ov.get("days_to_50pct") is not None else "—"),
    ]
    # kpi_list = dbc.Row([
    #     dbc.Col(dbc.ListGroup([dbc.ListGroupItem([html.Strong(k), html.Span(" — " + v, className="text-muted")]) for k, v in kpis]), md=12)
    # ])
    # overview = dbc.Row([
    #     dbc.Col(html.Div([html.Div(className="d-flex align-items-center", children=[card_left, title])]), md=6),
    #     dbc.Col(kpi_list, md=6)
    # ])
    kpi_defs = [
        {
            "key": "first_play",
            "label": "Zum ersten Mal gehört",
            "value": ov["first_play"][:10] if ov.get("first_play") else "—",
            "help": "Der erste Stream im gewählten Zeitraum.",
        },
        {
            "key": "last_play",
            "label": "Zuletzt gehört",
            "value": ov["last_play"][:10] if ov.get("last_play") else "—",
            "help": "Der letzte Stream im gewählten Zeitraum.",
        },
        {
            "key": "unique_days",
            "label": "An so vielen Tagen gehört",
            "value": f"{ov['unique_days']}",
            "help": "An wie vielen verschiedenen Tagen du den Song mindestens einmal gehört hast.",
        },
        {
            "key": "longest_streak_days",
            "label": "Längste Serie",
            "value": f"{ov['longest_streak_days']} Tage",
            "help": "So viele Tage am Stück hast du den Song mindestens einmal gehört.",
        },
        {
            "key": "median_gap_days",
            "label": "Typischer Abstand",
            "value": f"{ov['median_gap_days']} d" if ov.get("median_gap_days") is not None else "—",
            "help": "So lange liegt normalerweise zwischen zwei Streams (Median: die Hälfte der Abstände ist kürzer).",
        },
        {
            "key": "mean_gap_days",
            "label": "Durchschnittlicher Abstand",
            "value": f"{ov['mean_gap_days']} d" if ov.get("mean_gap_days") is not None else "—",
            "help": "Der Durchschnitt aller Abstände zwischen zwei Streams. Lange Pausen ziehen ihn stark nach oben.",
        },
        {
            "key": "current_silence_days",
            "label": "Seit dem letzten Mal",
            "value": f"{ov['current_silence_days']} d" if ov.get("current_silence_days") is not None else "—",
            "help": "So viele Tage ist der letzte Stream her (bis zum Ende des Zeitraums bzw. bis heute).",
        },
        {
            "key": "days_to_50pct",
            "label": "Halbzeit nach",
            "value": f"{ov['days_to_50pct']} d" if ov.get("days_to_50pct") is not None else "—",
            "help": "Nach so vielen Tagen ab dem ersten Stream hattest du die Hälfte aller Streams erreicht.",
        },
    ]

    kpi_items = []
    kpi_tooltips = []
    for k in kpi_defs:
        item, tip = make_kpi_item(SCOPE, k["key"], k["label"], k["value"], k["help"])
        kpi_items.append(item)
        kpi_tooltips.append(tip)

    kpi_list = html.Div([
        dbc.ListGroup(kpi_items),
        # Tooltips müssen im Layout vorhanden sein (können außerhalb der ListGroup liegen)
        *kpi_tooltips
    ])

    overview = dbc.Row([
        dbc.Col(html.Div([html.Div(className="d-flex align-items-center", children=[card_left, title])]), md=6),
        dbc.Col(kpi_list, md=6)
    ])

    # Lifecycle
    wk = song_weekly_counts(chosen_id, start_date, end_date, int(cache_ver or 0))
    fig_lc = build_song_lifecycle_figure(wk, dark)
    lifecycle = dcc.Graph(figure=fig_lc, config={"displayModeBar": True})

    # Listening Clock
    clk = song_clock(chosen_id, start_date, end_date, int(cache_ver or 0))
    fig_clk = build_listening_clock_figure(clk, dark)
    clock = dcc.Graph(figure=fig_clk, config={"displayModeBar": False})

    # Inter-Arrival
    ia = song_interarrival(chosen_id, start_date, end_date, int(cache_ver or 0))
    fig_ia = build_interarrival_hist_figure(ia, dark)
    interarrival = dcc.Graph(figure=fig_ia, config={"displayModeBar": True})

    # Heatmap für gewähltes Jahr
    if not year:
        hm_child = dbc.Alert("Wähl ein Jahr aus, dann siehst du hier den Kalender.", color="info")
    else:
        df_daily = cached_daily_song_counts(chosen_id, int(year), int(cache_ver or 0))
        fig_hm = build_song_heatmap_figure(df_daily, int(year), dark=dark)
        hm_child = dcc.Graph(figure=fig_hm, config={"displayModeBar": True})

    return overview, lifecycle, clock, interarrival, hm_child


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
