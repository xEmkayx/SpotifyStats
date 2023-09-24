# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import threading

import dash
import dash_bootstrap_components as dbc
import plotly.io as pio
from dash import Dash
from dash import html, DiskcacheManager
from dash_bootstrap_templates import ThemeChangerAIO

from analysis.graphics.webapp.components.dataframe_store import DataframeStore
# import diskcache
from analysis.graphics.webapp.df_files import dataframe_loader
import asyncio

from pathlib import Path
import os
from analysis.graphics.webapp.components.navbar import Navbar

from analysis.graphics.webapp.helpers import dataframe_helpers

default_theme = dbc.themes.LUX
pio.templates.default = "plotly_dark"

available_themes = [
    dbc.themes.CERULEAN, dbc.themes.COSMO, dbc.themes.CYBORG, dbc.themes.DARKLY,
    dbc.themes.FLATLY,
    dbc.themes.JOURNAL,
    dbc.themes.LITERA, dbc.themes.LUMEN, dbc.themes.LUX,
    dbc.themes.MATERIA, dbc.themes.MINTY, dbc.themes.MORPH,
    dbc.themes.PULSE,
    dbc.themes.QUARTZ,
    dbc.themes.SANDSTONE, dbc.themes.SIMPLEX, dbc.themes.SKETCHY, dbc.themes.SLATE,
    dbc.themes.SOLAR, dbc.themes.SPACELAB, default_theme,  # dbc.themes.SUPERHERO,
    dbc.themes.UNITED,
    dbc.themes.VAPOR,
    dbc.themes.YETI,
    dbc.themes.ZEPHYR
]

pages_folder = os.path.join(Path(__file__).parent, 'analysis/graphics/webapp/pages')
assets_folder = os.path.join(Path(__file__).parent, 'analysis/graphics/webapp/assets')

theme_change = ThemeChangerAIO(aio_id="all-themes",
                               radio_props={
                                   'value': default_theme
                               })

dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"

store = DataframeStore()

# cache = diskcache.Cache("./cache")
# background_callback_manager = DiskcacheManager(cache)

app = dash.Dash(__name__, use_pages=True, assets_ignore='./assets/*.css',
                external_stylesheets=[default_theme,
                                      dbc_css
                                      ],
                pages_folder=pages_folder,
                assets_folder=assets_folder,
                # external_stylesheets=[dbc.themes.SUPERHERO])  # vapor, superhero, quartz, solar, slate
                # background_callback_manager=background_callback_manager
                )


button_group = dbc.ButtonGroup(
    [
        dbc.Button("Left", color="danger", outline=True),
        dbc.Button("Middle", color="warning", outline=True),
        dbc.Button("Right", color="success", outline=True),
    ]
)

navbar = Navbar(dash.page_registry.values())

app.layout = dbc.Container(
    [store.render(), navbar, theme_change, dash.page_container], fluid=True, className="dbc"  # theme_toggle
)


def main(reload_df_on_start: bool = True):
    # print('Starting webapp...')
    if reload_df_on_start:
        _ = dataframe_loader.reload_df_store()
        # dataframe_getter.reload_dfs()
        # analysis.graphics.webapp.helpers.setting_functions.reset_df()
    app.run(debug=True, threaded=True)


if __name__ == '__main__':
    # dataframe_helpers.load_default_df()
    threading.Thread(target=main(False)).start()
    # main(False)
