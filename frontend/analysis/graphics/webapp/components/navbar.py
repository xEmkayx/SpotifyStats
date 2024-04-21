import dash_bootstrap_components as dbc
from dash import html
import os
from pathlib import Path

pages_folder = os.path.join(Path(__file__).parent.parent, 'pages')


def init_dd_artists(pages):
    dropdown_artists = html.Div(
        [
            dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem(f'{page["name"]}', href=f'{page["path"]}')
                    # for page in dash.page_registry.values() if str(page).__contains__('artist')
                    for page in pages if str(page).__contains__('artist')
                ],
                label="Artists",
            ),
        ]
    )
    return dropdown_artists


def init_dd_albums(pages):
    dropdown_albums = html.Div(
        [
            dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem(f'{page["name"]}', href=f'{page["path"]}')
                    for page in pages if str(page).__contains__('album')
                ],
                label="Albums",
            ),
        ]
    )
    return dropdown_albums


def init_dd_songs(pages):
    dropdown_songs = html.Div(
        [
            dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem(f'{page["name"]}', href=f'{page["path"]}')
                    for page in pages if str(page).__contains__('song')
                ],
                label="Songs",
            ),
        ]
    )
    return dropdown_songs


def init_dd_sunbursts(pages):
    dropdown_sunbursts = html.Div(
        [
            dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem(f'{page["name"]}', href=f'{page["path"]}')
                    for page in pages if str(page).__contains__('sunburst')
                ],
                label="Sunbursts",
            ),
        ]
    )
    return dropdown_sunbursts


def init_dd_single(pages):
    dropdown_single = html.Div(
        [
            dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem(f'{page["name"]}', href=f'{page["path"]}')
                    for page in pages if str(page).__contains__('single')
                ],
                label="Single",
            ),
        ]
    )
    return dropdown_single


def init_dd_line(pages):
    dropdown_line = html.Div(
        [
            dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem(f'{page["name"]}', href=f'{page["path"]}')
                    for page in pages if str(page).__contains__('line')
                ],
                label="Line charts",
            ),
        ]
    )
    return dropdown_line


def init_dd_bar(pages):
    dropdown_bar = html.Div(
        [
            dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem(f'{page["name"]}', href=f'{page["path"]}')
                    for page in pages if str(page).__contains__('bar')
                ],
                label="Bar charts",
            ),
        ]
    )
    return dropdown_bar


def init_dd_all(pages):
    dropdown_all = html.Div(
        [
            dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem(f'{page["name"]}', href=f'{page["path"]}')
                    for page in pages
                ],
                label="All",
            ),
        ]
    )
    return dropdown_all


def init_dd_settings(pages):
    settings = html.Div(
        [
            dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem(f'{page["name"]}', href=f'{page["path"]}')
                    for page in pages if str(page).__contains__('settings')
                ],
                label='Settings'
            ),
        ]
    )
    return settings


def init_all_dropdowns(pages):
    all_dds = [
        init_dd_settings(pages),
        init_dd_all(pages),
        init_dd_single(pages),
        init_dd_songs(pages),
        init_dd_artists(pages),
        init_dd_albums(pages),
        init_dd_sunbursts(pages),
        init_dd_line(pages),
        init_dd_bar(pages)
    ]
    return all_dds


class Navbar(dbc.NavbarSimple):
    def __init__(self, pages):
        super().__init__(
            className="navbar",
            children=[
                dbc.NavItem(item) for item in init_all_dropdowns(pages)
            ],
            brand="Spotify Stats",  # NavbarSimple
            brand_href="#",
            color="primary",
            dark=True,
        )
