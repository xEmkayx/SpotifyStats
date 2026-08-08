from dash import html, dcc
import pandas as pd

from frontend.analysis.graphics.webapp.helpers.consts import DATAFRAME_STORE_ID
from frontend.analysis.graphics.webapp.select_statements import allrounder


class DataframeStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataframeStore, cls).__new__(cls)
            cls.store = dcc.Store(id=DATAFRAME_STORE_ID, data=cls.load_initial_dataframe())
        return cls._instance

    @staticmethod
    def initialize():
        if DataframeStore._instance is None:
            store_data = DataframeStore.load_initial_dataframe()
            DataframeStore().store = dcc.Store(id=DATAFRAME_STORE_ID, data=store_data)

    @staticmethod
    def load_initial_dataframe():
        return get_default_df()

    @classmethod
    def get_store(cls):
        return cls()._instance.store


def get_default_df():
    # Query the DB directly instead of the CSV cache detour (the CSV was written
    # with a Windows path and never exists in the container).
    df = allrounder()
    return df.to_dict('records')
