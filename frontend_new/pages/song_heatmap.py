from datetime import date

import dash
import dash_bootstrap_components as dbc
from dash import dcc, Input, Output, State, callback, no_update, html

from frontend_new.components.charts import build_song_heatmap_figure
from frontend_new.components.empty_state import skeleton_graph
from frontend_new.components.filters import build_filter_panel, dropdown, sidebar_id, siid, stid, \
    fid, aid, text_input, make_sidebar_layout
from frontend_new.services.song_heatmap import cached_daily_song_counts
from frontend_new.services.song_search import search_songs, get_song_option_by_id

SCOPE = "song-heatmap"
dash.register_page(__name__, path="/song-heatmap", name="Song Heatmap")


def _year_options(n=6):
    this = date.today().year
    return [{"label": str(y), "value": y} for y in range(this, this - n, -1)]


def layout():
    filters = build_filter_panel(
        scope=SCOPE,
        controls=[
            dropdown(SCOPE, "song", "Song", options=[], multi=False,
                     placeholder="Tippe zum Suchen (min. 2 Zeichen)"),
            text_input(SCOPE, "song_id", "Song-ID (optional)", placeholder="z. B. 4uLU6hMCjMI75M1A2tKUQC"),
            dropdown(SCOPE, "year", "Jahr", options=_year_options(), multi=False, placeholder="Jahr wählen"),
        ],
        with_apply=True,
        variant="plain",
    )
    right = [
        dbc.Card([
            dbc.CardHeader("Hörhistorie (Kalender)"),
            dbc.CardBody(
                dcc.Loading(type="default", children=html.Div(id="song-hm", children=skeleton_graph()))
            ),
        ])
    ]
    return make_sidebar_layout(scope=SCOPE, sidebar_children=filters, content_children=right, title="Filter")


@callback(
Output(fid(SCOPE, "song"), "value"),
Output(fid(SCOPE, "song"), "options"),
Input(fid(SCOPE, "song"), "search_value"),
Input(fid(SCOPE, "song_id"), "value"),
State(fid(SCOPE, "song"), "options"),
prevent_initial_call=True
)
def update_song_selector(search_value, song_id, options):
    # herausfinden, welcher Input getriggert hat
    prop = dash.ctx.triggered[0]["prop_id"].split(".")[-1] if dash.ctx.triggered else None

    if prop == "search_value":
        q = (search_value or "").strip()
        if len(q) < 2:
            return no_update, no_update  # nichts ändern
        return no_update, search_songs(q, limit=50)

    # sonst: song_id geändert
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
Output("song-hm", "children"),
Input(aid(SCOPE), "n_clicks"),
State(fid(SCOPE, "song"), "value"),
State(fid(SCOPE, "song_id"), "value"),   # <- neu
State(fid(SCOPE, "year"), "value"),
State("theme", "data"),
State("cache-version", "data"),
prevent_initial_call=True
)
def update_heatmap(n, song_id_dropdown, song_id_text, year, theme, cache_ver):
    chosen_id = (song_id_dropdown or song_id_text or "").strip()
    if not chosen_id or not year:
        return dbc.Alert("Bitte Song und Jahr wählen.", color="info")
    df = cached_daily_song_counts(chosen_id, int(year), int(cache_ver or 0))
    fig = build_song_heatmap_figure(df, int(year), dark=(theme == "dark"))
    return dcc.Graph(figure=fig, config={"displayModeBar": True})


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
