import dash
from dash import html
from dash_bootstrap_templates import ThemeChangerAIO
from analysis.graphics.webapp.components.selection_box import SelectionBox

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
