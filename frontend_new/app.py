from flask import Flask
import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from config import CACHE_TIMEOUT_SEC, BOOTSTRAP_THEME
from frontend_new.core.extensions import init_extensions
import components.navbar as navbar
from dash.dependencies import ClientsideFunction
# Dash Pages aktivieren

server = Flask(__name__)
init_extensions(server, cache_timeout_sec=CACHE_TIMEOUT_SEC)
# dcc.Store(id="theme", data="light")

# Pages explizit importieren, damit sie registriert sind
# import pages.home  # noqa
# import pages.top_songs  # noqa

external_stylesheets = [getattr(dbc.themes, BOOTSTRAP_THEME), dbc.icons.BOOTSTRAP]
app = dash.Dash(
    __name__,
server=server,              # wichtig
use_pages=True,
external_stylesheets=external_stylesheets,
suppress_callback_exceptions=True,
)

app.layout = html.Div([
    dcc.Location(id="url"),
    dcc.Store(id="cache-version", data=0),
    dcc.Store(id="theme", data="dark"),  # <- NEU
    navbar.make_navbar(),
    dash.page_container
])

app.clientside_callback(
    ClientsideFunction(namespace="theme", function_name="detect"),
    Output("theme", "data"),
    Input("url", "pathname")
)


@app.callback(Output("cache-version", "data"),
Input("btn-refresh", "n_clicks"),
State("cache-version", "data"),
prevent_initial_call=True)
def bump_cache_version(n, current):
    return (current or 0) + 1


if __name__ == "__main__":
    app.run(debug=True, port=8081)
