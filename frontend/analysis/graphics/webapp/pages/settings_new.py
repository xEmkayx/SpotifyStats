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

# layout = html.Div(
#     # className='',
#     children=[
#         reload_button
#     ]
# )
layout = html.Div(
    [
        reload_button,
        html.Div(id='div-reload-feedback')  # Feedback Bereich für Benachrichtigungen
    ]
)


# TODO: update doesnt work properly
@callback(
    Output(DATAFRAME_STORE_ID, 'data'),
    Output('div-reload-feedback', 'children'),  # Feedback Bereich für Benachrichtigungen
    [Input('btn-reload-df', 'n_clicks')],
    prevent_initial_call=True
)
def reload_df(n_clicks):
    if n_clicks > 0:
        try:
            df = dataframe_loader.reload_df_store()
            feedback_message = dbc.Alert("Data successfully reloaded!", color="success")
            return df.to_dict('records'), feedback_message
        except Exception as e:
            feedback_message = dbc.Alert(f"Failed to reload data: {str(e)}", color="danger")
            return dash.no_update, feedback_message

    return dash.no_update, dash.no_update
