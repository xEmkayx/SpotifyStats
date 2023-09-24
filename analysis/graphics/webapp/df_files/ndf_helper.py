from datetime import date, datetime
import pandas as pd
from analysis.graphics.webapp.helpers import summary_cards, time_functions
from analysis.graphics.webapp.df_files import dataframe_loader
from analysis.graphics.webapp.helpers.df_filenames import *


def date_mask(start_date: str, end_date: str, df: pd.DataFrame):
    df['Played at'] = pd.to_datetime(df['Played at'], format='%Y-%m-%dT%H:%M')
    mask = (df['Played at'] >= start_date) & (df['Played at'] <= end_date)
    return mask


def get_top_songs_df(df: pd.DataFrame, start_date: str = str(date(2010, 1, 1)), end_date: str = str(date.today()),
                     sorted_by_mins: bool = False):
    # df = get_default_dataframe()
    mask = date_mask(start_date, end_date, df)
    ndf = df.loc[mask]

    if sorted_by_mins:
        df_combined = normalize_to_minutes(ndf.copy(deep=True))
    else:
        gr = ndf.groupby('Played at').agg(
            {'Song-ID': 'first', 'Song': 'first', 'Artist': ', '.join, 'Artist-ID': ', '.join,
             'Album': 'first', 'Album-ID': 'first', 'Song Length': 'first'})

        counted = gr.value_counts('Song-ID').rename({1: 'Song-ID', 2: 'Stream Count'}).sort_index().reset_index()
        counted.set_axis(['Song-ID', 'Stream Count'], axis=1, inplace=True)
        rest = gr.reset_index().drop('Played at', axis=1).drop_duplicates('Song-ID').sort_values('Song-ID')
        df_combined = pd.merge(counted, rest).sort_values('Stream Count', ascending=False)
    return df_combined


def get_top_artists(df: pd.DataFrame, start_date: str = str(date(2010, 1, 1)), end_date: str = str(date.today())):
    mask = date_mask(start_date, end_date, df)
    ndf = df.loc[mask]

    gr = ndf.groupby(['Artist', 'Artist-ID'], as_index=False).size()
    df_sorted = gr.sort_values(by=['size'], ascending=False)
    df_sorted.rename({1: 'Artist', 2: 'Artist-ID', 3: 'Stream Count'})
    df_sorted.set_axis(['Artist', 'Artist-ID', 'Stream Count'], axis=1, inplace=True)

    return df_sorted


def get_top_albums(df: pd.DataFrame, start_date: str = str(date(2010, 1, 1)), end_date: str = str(date.today())):
    mask = date_mask(start_date, end_date, df)
    ndf = df.loc[mask]

    gr = ndf.groupby('Played at').agg({'Album': 'first', 'Album-ID': 'first',
                                       'Artist': ', '.join, 'Artist-ID': ', '.join,
                                       })
    counted = gr.value_counts('Album-ID').rename({1: 'Album-ID', 2: 'Stream Count'}).sort_index().reset_index()
    counted.set_axis(['Album-ID', 'Stream Count'], axis=1, inplace=True)
    rest = gr.reset_index().drop('Played at', axis=1).drop_duplicates('Album-ID').sort_values('Album-ID')
    df_combined = pd.merge(counted, rest).sort_values('Stream Count', ascending=False)
    return df_combined


def normalize_to_minutes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes a DataFrame, so it's sorted by its total streamed minutes
    :param df: DataFrame to normalize
    :return: normalized DataFrame
    """
    ndf = df
    gr = ndf.groupby('Played at').agg(
        {'Song-ID': 'first', 'Song': 'first', 'Artist': ', '.join, 'Artist-ID': ', '.join, 'Song Length': 'first',
         'Album': 'first', 'Album-ID': 'first'})

    counted = gr.value_counts('Song-ID').rename({1: 'Song-ID', 2: 'Stream Count'}).sort_index().reset_index()

    gr['Song Length'] = pd.to_datetime(gr['Song Length'], format='%H:%M:%S', errors='coerce').fillna(
        pd.to_datetime(gr['Song Length'],
                       format='%M:%S'))

    gr['Song Length'] = gr['Song Length'].dt.time
    gr['Song Length'] = gr['Song Length'].astype(str)

    counted.set_axis(['Song-ID', 'Stream Count'], axis=1, inplace=True)
    rest = gr.reset_index().drop('Played at', axis=1).drop_duplicates('Song-ID').sort_values('Song-ID')
    df_combined = pd.merge(counted, rest).sort_values('Stream Count', ascending=False)

    df_combined['Dauer Sekunden'] = pd.to_timedelta(df_combined['Song Length']).dt.total_seconds()
    df_combined['Streamed Mins'] = df_combined['Stream Count'] * (df_combined['Dauer Sekunden'] / 60)

    # df_combined['Streamed Mins'] = df_combined['Streamed Mins'].apply(lambda x: '{:.2f}'.format(x))

    df_combined = df_combined.sort_values('Streamed Mins', ascending=False)
    return df_combined


def get_played_at_table(df: pd.DataFrame, start_date: str = str(date(2010, 1, 1)), end_date: str = str(date.today())):
    mask = date_mask(start_date=start_date, end_date=end_date, df=df)
    ndf = df.loc[mask]
    gr = ndf.groupby('Played at').agg(
        {'Song-ID': 'first', 'Song': 'first', 'Artist': ', '.join, 'Artist-ID': ', '.join, 'Song Length': 'first',
         'Album': 'first', 'Album-ID': 'first'})

    gr = gr.reset_index()[::-1]
    return gr
