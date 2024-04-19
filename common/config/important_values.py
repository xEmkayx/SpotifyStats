"""
    Important static and constant key values
"""
import logging
import os
import sys
from pathlib import Path

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

"""Database table names"""
# database name -> database (see below)
# todo: exchange string values in .py files for these constants
songs_tab_name = 'songs'
albums_tab_name = 'albums'
artists_tab_name = 'artists'
album_artists_tab_name = 'album_artists'
artists_songs_tab_name = 'artists_songs'
stream_history_tab_name = 'stream_history'

"""Database Field Amounts"""
db_artist_cols = 2
db_stream_history_cols = 2
db_albums_cols = 2
db_songs_cols = 4
db_as_cols = 2
db_album_artists_cols = 2

"""Files"""
last_streams_name = 'last_streams.json'
last_streams_rel = os.path.join('temp_files', last_streams_name)
last_streams_dir = os.path.join(parentdir, last_streams_rel)

"""Logging values"""
project_root = Path(__file__).parent.parent
log_level = logging.INFO
log_format = '%(asctime)s %(levelname)s: %(message)s'
log_datefmt = '%Y-%m-%d %H:%M:%S'
log_filename = os.path.join(project_root, 'logs', 'log.txt')

if __name__ == '__main__':
    print(project_root)
    print(log_filename)
