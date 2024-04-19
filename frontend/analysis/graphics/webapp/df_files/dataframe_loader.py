import pandas as pd
from frontend.analysis.graphics.webapp.helpers import df_temp_write_files
from frontend.analysis.graphics.webapp.helpers.df_filenames import *


# df = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')


def reload_df_store():
    df_temp_write_files.write_allrounder()
    sdf = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')
    return sdf
