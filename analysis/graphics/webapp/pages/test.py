import dash
import plotly.express as px
from dash import html, dcc, callback, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url
from analysis.graphics.webapp.components.selection_box import SelectionBox
import os

from analysis.graphics.webapp.helpers import name_helpers

dash.register_page(__name__)

theme_change = ThemeChangerAIO(aio_id="theme")

sb = SelectionBox(name_helpers.get_current_file_name(__file__))

layout = html.Div(
    children=[
        html.H1('Testpage'),
        sb.render()
    ]
)
