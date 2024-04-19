import dash
import dash_bootstrap_components as dbc
from dash import html, callback, Input, Output, State

from frontend.analysis.graphics.webapp.df_files import dataframe_loader
from frontend.analysis.graphics.webapp.helpers.consts import *

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

