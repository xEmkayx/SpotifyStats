"""
    Insert your streaming history (the one you get from the support) to your database.
    (this script is intended to be run manually. May be updated to run automatically)
    # TODO
"""
import json
import os
import traceback

import mysql.connector
import numpy as np
import pandas as pd

import tools.DBOperations.dboperations
from tools.last_streamed_methods import clean_item

# TODO: Aufräumen und pushen
file_loc = r'C:\Users\Markus\PycharmProjects\Spotify_Stats\spotify_scripts\DL_Data\MyData'
# filename = 'StreamingHistoryAlle'
filename = 'StreamingHistory1'
fileending = '.json'

dbops = tools.DBOperations.dboperations.DBOperations()


def get_unliked_tracks():
    # all_tracks = dict(dbops.select_from_table('songs', 'song_name, song_id'))
    # all_tracks = dbops.select_from_table('songs', 'song_id, song_name')
    all_tracks = np.array(dbops.select_from_table('songs', 'song_id, song_name'))
    unliked_tracks = []
    try:
        for i in range(0, 9):
            with open(os.path.join(file_loc, f'{filename}{fileending}'), 'r', encoding="utf-8") as f:
                jf = json.load(f)
                for entry in jf:
                    artist_name = clean_item(json.dumps(entry['artistName']))
                    track_name = clean_item(json.dumps(entry['trackName']))
                    played_at = clean_item(json.dumps(entry['endTime']))
                    if not (artist_name.__contains__("Unknown Artist")) \
                            and not (track_name.__contains__("Unknown Track")):
                        if track_name in all_tracks:
                            pass
                        else:
                            unliked_tracks.append((artist_name, track_name))
                            # pass
                        # print(f'{played_at} -/-/- {artist_name} -- {track_name}')
                    else:
                        # print('Unknown')
                        pass
        return unliked_tracks

    except FileNotFoundError:
        print('File not Found')
        pass


# print(all_tracks)
# with open(r'C:\Users\Markus\PycharmProjects\Spotify_Stats\spotify_scripts\BigOperations\unliked_songs.txt', 'w') as f:
#     for i in unliked_tracks:
#         f.write(f'{i[0]} - {i[1]}\n')
# for i in range(0, 9):
#     print(unliked_tracks[i])
# print(unliked_tracks[10])
# print(all_tracks[0])
# print(unliked_tracks[0])
# print(unliked_tracks[1])
# print(unliked_tracks[2])
# print(all_tracks[1])

# dbops.cursorObject.close()


def write_history_to_db():
    dup_counter = 0
    col_names = ['song_id', 'song_name', 'artist_name']
    # df = dbops.select_from_table('songs', 'song_id, song_name')
    df = dbops.dl_history_query()
    temp_list = []
    for ds in df:
        temp_list.append([ds[0], ds[1], ds[2]])

    all_db_tracks = pd.DataFrame(temp_list, columns=col_names)

    # print(all_db_tracks)
    # streaming history tracks
    sh_tracks = []
    problemkinder = []
    # all_tracks = np.array(dbops.dl_history_query())
    try:
        with open(os.path.join(file_loc, f'{filename}{fileending}'), 'r', encoding="utf-8") as f:
            jf = json.load(f)
            for entry in jf:
                song_id = 0
                artist_name = clean_item(json.dumps(entry['artistName']))
                track_name = clean_item(json.dumps(entry['trackName']))
                played_at = clean_item(json.dumps(entry['endTime']))

                t_namen_indizes = all_db_tracks.index[all_db_tracks['song_name'] == track_name].tolist()
                for i in t_namen_indizes:
                    tmp_row = all_db_tracks.iloc[[i]]
                    # print(tmp_row['artist_name'])
                    an = tmp_row['artist_name']
                    # s_id = tmp_row['song_id']
                    # print(an.iloc[0])
                    if an.iloc[0] == artist_name:
                        song_id = tmp_row['song_id'].iloc[0]
                        # print(song_id)
                        # print((played_at, song_id))
                        try:
                            dbops.write_to_stream_history((played_at, song_id))
                            print(f'Wrote {artist_name} - {track_name} at {played_at} to DB ')
                        except mysql.connector.IntegrityError:
                            dup_counter += 1
                            print(f'{song_id}:\tDuplicate key error. Passing...')
                            print(f'Duplicate Counter: \t\t\t {dup_counter}')
                            pass

                # time.sleep(60)

    except FileNotFoundError:
        print('File not Found')
        pass
    except:
        traceback.print_exc()
    finally:
        dbops.close_all()


if __name__ == '__main__':
    write_history_to_db()
