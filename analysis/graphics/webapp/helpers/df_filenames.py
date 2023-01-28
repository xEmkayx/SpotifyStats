import os
import sys

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

fn_df_top_album_streams = 'top_album_streams'
fn_df_all_streams = 'all_streams'
fn_df_anz_streams = 'anz_album_streams'
fn_df_anz_album_streams = 'anz_album_streams'
fn_df_anz_top_album_streams = 'anz_top_albums_streams'
fn_df_anz_single_album_streams = 'anz_single_album_streams'
fn_df_stream_history = 'stream_history'
fn_df_anz_all_artist_streams = 'anz_all_artist_streams'
fn_df_anz_single_artist_streams = 'anz_single_artist_streams'
fn_df_anz_single_song_streams = 'anz_single_song_streams'
fn_df_allrounder = 'allrounder'

df_common_path = os.path.join(parentdir, 'df_files')
