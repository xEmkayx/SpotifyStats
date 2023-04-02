from analysis.graphics.webapp.helpers.df_filenames import *
import pandas as pd
from analysis.graphics.webapp.helpers import setting_functions

df = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')


def get_default_dataframe() -> pd.DataFrame:
    return df.copy(deep=True)


def reload_dataframe():
    global df
    setting_functions.reset_df()
    df = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')


async def init():
    global df
    df = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')
