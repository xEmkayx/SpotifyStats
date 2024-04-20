from dash import html, dcc
import pandas as pd

from frontend.analysis.graphics.webapp.helpers.consts import DATAFRAME_STORE_ID
from frontend.analysis.graphics.webapp.helpers.df_filenames import *


class DataframeStore:
    def __init__(self):
        self.store_id = DATAFRAME_STORE_ID
        self.store_item = init_store(self.store_id)

    def render(self):
        return html.Div(
            self.store_item
        )


def init_store(item_id):
    store = dcc.Store(
        id=item_id,
        data=get_default_df(),
    )
    return store


def get_default_df():
    df = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv', index_col=[0])
    return df.to_dict('records')