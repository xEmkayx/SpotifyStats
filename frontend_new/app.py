from flask import Flask
import dash
from dash import html, dcc, Input, Output, ctx
import dash_bootstrap_components as dbc
from dash.dependencies import ClientsideFunction

from frontend_new.config import CACHE_TIMEOUT_SEC, BOOTSTRAP_THEME, DATA_VERSION_TTL_SEC, DASH_HOST, DASH_PORT, \
    DASH_DEBUG
from frontend_new.core.extensions import init_extensions

server = Flask(__name__)
init_extensions(server, cache_timeout_sec=CACHE_TIMEOUT_SEC)

# Erst nach init_extensions importieren: data_version nutzt den Cache
from frontend_new.core.data_version import data_version, bump_data_version  # noqa: E402
import frontend_new.components.navbar as navbar  # noqa: E402

external_stylesheets = [getattr(dbc.themes, BOOTSTRAP_THEME), dbc.icons.BOOTSTRAP]
app = dash.Dash(
    __name__,
    server=server,
    use_pages=True,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
    title="Spotify Stats",
)


def serve_layout():
    # Als Funktion: wird bei jedem Seitenaufruf ausgewertet -> aktuelle Datenversion
    return html.Div([
        dcc.Location(id="url"),
        dcc.Store(id="cache-version", data=data_version()),
        dcc.Store(id="theme", data="dark"),
        # Offene Tabs bekommen neue Daten mit, ohne dass jemand Refresh drückt
        dcc.Interval(id="data-version-poll", interval=DATA_VERSION_TTL_SEC * 1000),
        navbar.make_navbar(),
        dash.page_container,
    ])


app.layout = serve_layout

app.clientside_callback(
    ClientsideFunction(namespace="theme", function_name="detect"),
    Output("theme", "data"),
    Input("url", "pathname")
)


@app.callback(
    Output("cache-version", "data"),
    Input("btn-refresh", "n_clicks"),
    Input("data-version-poll", "n_intervals"),
    prevent_initial_call=True
)
def update_cache_version(n_refresh, _n_poll):
    if ctx.triggered_id == "btn-refresh":
        return bump_data_version()
    return data_version()


if __name__ == "__main__":
    app.run(host=DASH_HOST, port=DASH_PORT, debug=DASH_DEBUG)
