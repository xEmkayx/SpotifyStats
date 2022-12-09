"""
    To prevent a lot of SQL requests, temp files are written to df_files
    (good for slower PCs, such as raspberry pis)
"""

import pandas as pd
from analysis.graphics.webapp.select_statements import *
from analysis.graphics.webapp.helpers.df_filenames import *


def write_allrounder():
    df_anz_single_song_streams = allrounder()
    df_anz_single_song_streams.to_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')


if __name__ == '__main__':
    write_allrounder()
