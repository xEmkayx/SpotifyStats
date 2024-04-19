"""
    Operations on the Database
"""

import mysql.connector
# from tools import important_values as iv
from multipledispatch import dispatch

from backend.tools.important_values import *
from private.connector_values import *
from backend.tools.errors.CustomExceptions import InvalidTupleLength


class DBOperations:

    def __init__(self):
        # values taken from tools.important_values
        self.mydb = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursorObject = self.mydb.cursor()

    def close_all(self) -> None:
        """
        Close all SQL connections
        """
        self.mydb.close()
        self.cursorObject.close()
        print('CursorObject Closed.')
        # mydb_glob.close()
        # DBOperations.mydb.close()
        # self.cursor.close()
        # self.mydb.close()
        # pass

    @dispatch(str, tuple)
    def execute_sql(self, sql: str, val: tuple) -> None:
        """
        execute sql statement with values
        :param str sql: SQL statement as string
        :param str val: values to be put into sql statement
        :return: None
        """
        self.cursorObject.execute(sql, val)
        self.mydb.commit()

    @dispatch(str)
    def execute_sql(self, sql) -> None:
        """
        execute sql statement without extra values
        :param str sql: SQL statement
        :return: - None
        """
        self.cursorObject.execute(sql)
        self.mydb.commit()
        # DBOperations.mydb.close()

    def write_to_stream_history(self, val: tuple) -> None:
        """
        Write to 'stream_history' table
        :param tuple val: Values as tuple with format (played_at, song_id)
        :return: None
        """
        try:
            if len(val) != db_stream_history_cols:
                raise InvalidTupleLength
        except InvalidTupleLength:
            print(f'The Tuple length is {len(val)}, while it should be '
                  f'{db_stream_history_cols}')

        sql = "INSERT INTO stream_history (played_at, song_id) " \
              "VALUES (%s, %s)"
        print(f'Stream History: {sql, val}')
        self.execute_sql(sql, val)

    def write_to_artists(self, val: tuple) -> None:
        """
        Write to 'artists' Table
        :param tuple val: Values as tuple with format (artist_id, artist_name)
        :return: None
        """
        try:
            if len(val) != db_artist_cols:
                raise InvalidTupleLength
        except InvalidTupleLength:
            print(f'The Tuple length is {len(val)}, while it should be {db_artist_cols}')

        sql = "INSERT INTO artists (artist_id, artist_name) VALUES (%s, %s)"
        print(f'Artist: {sql, val}')
        self.execute_sql(sql, val)

    def write_to_albums(self, val: tuple) -> None:
        """
        write to 'albums' table
        :param tuple val: Values as tuple with format (album_id, album_name)
        :return: None
        """
        try:
            if len(val) != db_albums_cols:
                raise InvalidTupleLength
        except InvalidTupleLength:
            print(f'The Tuple length is {len(val)}, while it should be {db_albums_cols}')

        sql = "INSERT INTO albums (album_id, album_name) " \
              "VALUES (%s, %s)"
        print(f'Album: {sql, val}')
        self.execute_sql(sql, val)

    def write_to_songs(self, val: tuple) -> None:
        """
        write to 'songs' table
        :param tuple val: Values as tuple with format (song_id, song_name, album_id, song_length)
        :return: None
        """
        try:
            if len(val) != db_songs_cols:
                raise InvalidTupleLength
        except InvalidTupleLength:
            print(f'The Tuple length is {len(val)}, while it should be {db_songs_cols}')

        sql = "INSERT INTO songs (song_id, song_name, album_id, song_length) " \
              "VALUES (%s, %s, %s, %s)"
        print(f'Song: {sql, val}')
        self.execute_sql(sql, val)

    def write_to_artists_songs(self, val: tuple) -> None:
        """
        Write to 'artists_songs' table
        :param tuple val: Values as tuple with format (song_id, artist_id)
        :return: None
        """
        try:
            if len(val) != db_as_cols:
                raise InvalidTupleLength
        except InvalidTupleLength:
            print(f'The Tuple length is {len(val)}, while it should be {db_as_cols}')

        sql = "INSERT INTO art_songs (song_id, artist_id) " \
              "VALUES (%s, %s)"
        print(f'A_S: {sql, val}')
        self.execute_sql(sql, val)

    def get_album_artists(self, val: tuple) -> None:
        """
        write to 'album_artists' table
        :param tuple val: Values as tuple with format (album_id, artist_id)
        :return: None
        """
        try:
            if len(val) != db_album_artists_cols:
                raise InvalidTupleLength
        except InvalidTupleLength:
            print(f'The Tuple length is {len(val)}, while it should be {db_album_artists_cols}')

        sql = "INSERT INTO album_artists (album_id, artist_id) " \
              "VALUES (%s, %s)"
        print(f'A_A: {sql, val}')
        self.execute_sql(sql, val)

    def clean_mn_tables(self) -> None:
        """
        Clean m-n tables
        :return: None
        """

        sql = "ALTER IGNORE TABLE artists_songs ADD UNIQUE(artist_id, song_id)"
        self.execute_sql(sql)
        sql = "ALTER IGNORE TABLE album_artists ADD UNIQUE(artist_id, album_id)"
        self.execute_sql(sql)

    @dispatch(str, str)
    def select_from_table(self, table: str, selector: str, ) -> tuple:
        """
        Select from table without arguments
        :param str table: Table from which to select from
        :param str selector: describe what should be selected
        :return: Database selection as tuple
        """

        sql = f'SELECT {selector} FROM {table};'
        self.cursorObject.execute(sql)
        return self.cursorObject.fetchall()

    @dispatch(str, str, str)
    # params: table, query arguments
    def select_from_table(self, table: str, selector: str, arguments: str) -> tuple:
        """
        Select selector from table with arguments
        :param str table: Table from which to select from
        :param str selector: describe what should be selected
        :param str arguments: define selection (everything after 'where' statement)
        :return: Database selection as tuple
        """

        sql = f'SELECT {selector} FROM {table} WHERE {arguments};'
        self.cursorObject.execute(sql)
        return self.cursorObject.fetchall()

    def update_song_length(self, song_length_old, song_length_new) -> None:
        """
        update song length (use if song lengths are invalid)
        Used in combination with spotify query
        :param str song_length_old: current (invalid) song_length
        :param str song_length_new: new (valid) song_length
        :return: None
       """

        sql = f'UPDATE songs SET song_length = \'{song_length_new}\' ' \
              f'WHERE song_length = \'{song_length_old}\';'
        self.execute_sql(sql)

    def update_artist_name(self, artist_id, artist_name: str) -> None:
        """
        updates artist name (use if artist names are invalid)
        Used in combination with spotify query
        :param str artist_id: artist_id
        :param str artist_name: artist_name
        :return: None
        """

        if artist_name.__contains__('"'):
            sql = f'UPDATE artists SET artist_name = \'{artist_name}\' ' \
                  f'WHERE artist_id = \'{artist_id}\';'
        else:
            sql = f'UPDATE artists SET artist_name = "{artist_name}" ' \
                  f'WHERE artist_id = "{artist_id}";'
        self.execute_sql(sql)

    def update_song_name(self, song_id: str, song_name: str) -> None:
        """
        updates song names (use if song names are invalid)
        Used in combination with spotify query
        :param str song_id: song_id
        :param str song_name: song_name
        :return: None
        """

        if song_name.__contains__('"') and song_name.__contains__("'"):
            song_name = song_name.replace('"', r'\"')
            sql = f'UPDATE songs SET song_name = "{song_name}" ' \
                  f'WHERE song_id = \'{song_id}\';'
        elif song_name.__contains__('"'):
            sql = f'UPDATE songs SET song_name = \'{song_name}\' ' \
                  f'WHERE song_id = \'{song_id}\';'
        else:
            sql = f'UPDATE songs SET song_name = "{song_name}" ' \
                  f'WHERE song_id = "{song_id}";'
        print(sql)
        self.execute_sql(sql)

    def update_album_name(self, album_id: str, album_name: str) -> None:
        """
        updates album names (use if album names are invalid)
        Used in combination with spotify query
        :param str album_id: album_id
        :param str album_name: album_name
        :return: None
        """

        if album_name.__contains__('"') and album_name.__contains__("'"):
            album_name = album_name.replace('"', r'\"')
            sql = f'UPDATE albums SET album_name = "{album_name}" ' \
                  f'WHERE album_id = \'{album_id}\';'
        elif album_name.__contains__('"'):
            sql = f'UPDATE albums SET album_name = \'{album_name}\' ' \
                  f'WHERE album_id = \'{album_id}\';'
        else:
            sql = f'UPDATE albums SET album_name = "{album_name}" ' \
                  f'WHERE album_id = "{album_id}";'
        print(sql)
        self.execute_sql(sql)

    def update_played_at(self, played_at_old: str, played_at_new: str) -> None:
        """
        updates values for played_at in stream_history table
        used if values don't match with current timezone (in my case: add 1h)
        used in combination with spotify query

        :param str played_at_old: old (invalid) value of played_at
        :param str played_at_new: new (valid) value of played_at
        :return: None
        """

        sql = f'UPDATE stream_history SET played_at = "{played_at_new}" ' \
              f'WHERE played_at = "{played_at_old}";'
        print(sql)
        self.execute_sql(sql)

    def dl_history_query(self):
        # a = r'select distinct played_at, song_name, artist_name, album_name, song_length from stream_history as sh left join songs on sh.song_id = songs.song_id left join artists_songs as ars on songs.song_id = ars.song_id left join artists on ars.artist_id = artists.artist_id left join albums on songs.album_id = albums.album_id group by played_at;'
        sql = 'SELECT DISTINCT songs.song_id, song_name, artist_name from songs left join artists_songs as ars on songs.song_id = ars.song_id left join artists on ars.artist_id = artists.artist_id;'
        print(sql)
        self.cursorObject.execute(sql)
        return self.cursorObject.fetchall()

    def custom_sql_statement(self, sql):
        """
        :param sql: full sql statement
        :return: selection
        """
        self.cursorObject.execute(sql)
        return self.cursorObject.fetchall()
