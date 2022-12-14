# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
from dash import Dash, dcc, html
from dash import Input, Output, html
import dash

import analysis.graphics.webapp.helpers.setting_functions
from helpers.colors import colors
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url
import plotly.io as pio

default_theme = dbc.themes.VAPOR
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

theme_change = ThemeChangerAIO(aio_id="all-themes")

dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"

app = dash.Dash(__name__, use_pages=True, assets_ignore='./assets/*.css',
                external_stylesheets=[default_theme,
                                      dbc_css
                                      ]
                # external_stylesheets=[dbc.themes.SUPERHERO])  # vapor, superhero, quartz, solar, slate
                )


dropdown_artists = html.Div(
    [
        dbc.DropdownMenu(
            [
                dbc.DropdownMenuItem(f'{page["name"]}', href=f'{page["path"]}')
                for page in dash.page_registry.values() if str(page).__contains__('artist')
            ],
            label="Artists",
        ),
    ]
)

dropdown_albums = html.Div(
    [
        dbc.DropdownMenu(
            [
                dbc.DropdownMenuItem(f'{page["name"]}', href=f'{page["path"]}')
                for page in dash.page_registry.values() if str(page).__contains__('album')
            ],
            label="Albums",
        ),
    ]
)

dropdown_songs = html.Div(
    [
        dbc.DropdownMenu(
            [
                dbc.DropdownMenuItem(f'{page["name"]}', href=f'{page["path"]}')
                for page in dash.page_registry.values() if str(page).__contains__('song')
            ],
            label="Songs",
        ),
    ]
)

dropdown_sunbursts = html.Div(
    [
        dbc.DropdownMenu(
            [
                dbc.DropdownMenuItem(f'{page["name"]}', href=f'{page["path"]}')
                for page in dash.page_registry.values() if str(page).__contains__('sunburst')
            ],
            label="Sunbursts",
        ),
    ]
)

dropdown_single = html.Div(
    [
        dbc.DropdownMenu(
            [
                dbc.DropdownMenuItem(f'{page["name"]}', href=f'{page["path"]}')
                for page in dash.page_registry.values() if str(page).__contains__('single')
            ],
            label="Single",
        ),
    ]
)

dropdown_line = html.Div(
    [
        dbc.DropdownMenu(
            [
                dbc.DropdownMenuItem(f'{page["name"]}', href=f'{page["path"]}')
                for page in dash.page_registry.values() if str(page).__contains__('line')
            ],
            label="Line charts",
        ),
    ]
)

dropdown_bar = html.Div(
    [
        dbc.DropdownMenu(
            [
                dbc.DropdownMenuItem(f'{page["name"]}', href=f'{page["path"]}')
                for page in dash.page_registry.values() if str(page).__contains__('bar')
            ],
            label="Bar charts",
        ),
    ]
)

dropdown_all = html.Div(
    [
        dbc.DropdownMenu(
            [
                dbc.DropdownMenuItem(f'{page["name"]}', href=f'{page["path"]}')
                for page in dash.page_registry.values()
            ],
            label="All",
        ),
    ]
)

settings = html.Div(
    [
        dbc.DropdownMenu(
            [
                dbc.DropdownMenuItem(f'{page["name"]}', href=f'{page["path"]}')
                for page in dash.page_registry.values() if str(page).__contains__('settings')
            ],
            label='Settings'
        ),
    ]
)

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(settings),
        dbc.NavItem(dropdown_all),
        dbc.NavItem(dropdown_single),
        dbc.NavItem(dropdown_songs),
        dbc.NavItem(dropdown_artists),
        dbc.NavItem(dropdown_albums),
        dbc.NavItem(dropdown_sunbursts),
        dbc.NavItem(dropdown_line),
        dbc.NavItem(dropdown_bar),
    ],
    brand="Spotify Stats",  # NavbarSimple
    brand_href="#",
    color="primary",
    dark=True,
)

button_group = dbc.ButtonGroup(
    [
        dbc.Button("Left", color="danger", outline=True),
        dbc.Button("Middle", color="warning", outline=True),
        dbc.Button("Right", color="success", outline=True),
    ]
)

app.layout = dbc.Container(
    [navbar, theme_change, dash.page_container], fluid=True, className="dbc"  # theme_toggle
)


if __name__ == '__main__':
    analysis.graphics.webapp.helpers.setting_functions.reset_df()
    app.run_server(debug=True)
