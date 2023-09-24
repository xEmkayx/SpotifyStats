import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import html, dcc, callback, Input, Output, no_update, State
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

from analysis.graphics.webapp.components.dataframe_store import DataframeStore
from analysis.graphics.webapp.components.single_type_selection import SingleTypeSelection
from analysis.graphics.webapp.helpers.consts import *
from analysis.graphics.webapp.df_files import dataframe_loader, ndf_helper

dash.register_page(__name__)

reload_button = dbc.Button(
    'Reload Dataframe',
    id='btn-reload-df',
    outline=True,
    color='primary',
    n_clicks=0
)

reload_text = html.Div(
    id='div-reload-text'
)

layout = html.Div(
    # className='',
    children=[
        reload_button
    ]
)

# TODO: update doesnt work properly
@callback(
    Output(DATAFRAME_STORE_ID, 'data'),
    Output('btn-reload-df', 'n_clicks'),
    # Input(DATAFRAME_STORE_ID, 'data'),
    State(DATAFRAME_STORE_ID, 'data'),
    Input('btn-reload-df', 'n_clicks')
)
def reload_df(store, btn_click):
    if btn_click == 1:
        print('if')
        df = dataframe_loader.reload_df_store()
        print('settings:')
        print(df.iloc[[-1]])
        print(df.shape[0])
        return df.to_dict('records'), 0
    else:
        print('else')
        print(store[-1])
        # df = dash.callback_context.states[DATAFRAME_STORE_ID]
        return store, 0
    # df = pd.DataFrame(df_store)

