import pandas as pd
from analysis.graphics.webapp.helpers.df_temp_write_files import write_allrounder
# from analysis.graphics.webapp.helpers.df_filenames import *


def reset_df():
    print('Started reloading DataFrame...')
    write_allrounder()
    print('Reloading DataFrame: Done')


def change_auth_data():
    pass


def change_dataframe_location():
    pass


