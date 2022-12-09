import dash
from dash import html, dcc, callback, Input, Output, no_update
from analysis.graphics.webapp.select_statements import *
from analysis.graphics.webapp.helpers.colors import colors
from analysis.graphics.webapp.helpers.df_filenames import *
from analysis.graphics.webapp.helpers.consts import *
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url
import dash_bootstrap_components as dbc
from analysis.graphics.webapp.helpers.setting_functions import *

dash.register_page(__name__)

layout = html.Div(
    children=[
        html.H1(
            'Graphs overview'
        ),
    ]
)
