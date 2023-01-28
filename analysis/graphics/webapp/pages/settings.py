import dash
import dash_bootstrap_components as dbc
from dash import html, callback, Input, Output, no_update

from analysis.graphics.webapp.helpers.setting_functions import *

dash.register_page(__name__)

reload_dataframe_div = html.Div(
    dbc.Button(
        'DataFrame neu laden',
        id='reset-df',
        outline=True,
        color='primary',
        n_clicks=0
    )
)

toast = dbc.Toast(
    [html.P(f"Button pressed", className="mb-0")],
    header="Toast",
    # duration=4000,
    dismissable=True,
    id='toast-settings',
    duration=20,
    icon="warning",
    is_open=False,
    style={"position": "fixed", "top": 66, "right": 10, "width": 350},
)

reset_label = html.Label(
    '',
    id='reset-label'
)

layout = html.Div(
    children=[
        html.H1(
            'Settings'
        ),
        reload_dataframe_div,
        reset_label,
        toast,
    ]
)


@callback(
    Output('reset-df', 'n_clicks'),
    Output('toast-settings', 'is_open'),
    Output('toast-settings', 'children'),
    Output('reset-label', 'children'),
    [Input('reset-df', 'n_clicks')],
)
def setting_actions(bclick):
    text = ''
    if bclick != 0:
        reset_df()
        ret = True
        text = f'DataFrame neu geladen'
    elif bclick == 0:
        ret = no_update
    else:
        ret = True

    return 0, ret, f'DataFrame neu geladen', text
