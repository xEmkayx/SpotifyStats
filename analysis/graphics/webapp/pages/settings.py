import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import html, callback, Input, Output, no_update

from analysis.graphics.webapp.components.dataframe_store import DataframeStore
from analysis.graphics.webapp.helpers import dataframe_helpers
from analysis.graphics.webapp.helpers.consts import DATAFRAME_STORE_ID
from analysis.graphics.webapp.helpers.setting_functions import *
from analysis.graphics.webapp.df_files import dataframe_loader

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

"""
@callback(
    Output('reset-df', 'n_clicks'),
    Output('toast-settings', 'is_open'),
    Output('toast-settings', 'children'),
    Output('reset-label', 'children'),
    Output(DATAFRAME_STORE_ID, 'data'),
    Input('reset-df', 'n_clicks'),
    prevent_initial_call=True
)
def setting_actions(bclick):
    text = ''
    sdf = pd.DataFrame(dash.callback_context.states[DATAFRAME_STORE_ID])
    print(type(sdf))
    print(sdf)
    if bclick != 0:
        # reset_df()
        # dataframe_loader.reload_dataframe()
        print('Started reloading DataFrame...')
        # dataframe_getter.reload_dfs()
        sdf = dataframe_loader.reload_df_store()
        print('Reloading DataFrame: Done')
        ret = True
        text = f'DataFrame neu geladen'
    elif bclick == 0:
        ret = no_update
    else:
        sdf = dataframe_loader.reload_df_store()
        ret = True

    return 0, ret, f'DataFrame neu geladen', text, sdf.to_dict('records')
"""
