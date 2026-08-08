import os

from frontend_new.config import DB_DIALECT


def played_at_cast_expr():
    if DB_DIALECT.lower() == "postgres":
        return "to_timestamp(sh.played_at, 'YYYY-MM-DD HH24:MI:SS.US')"
    return "STR_TO_DATE(sh.played_at, '%Y-%m-%d %H:%i:%s.%f')"


def length_seconds_expr(song_alias="s"):
    if DB_DIALECT.lower() == "postgres":
        return (
        f"EXTRACT(EPOCH FROM make_interval("
        f"mins = split_part({song_alias}.song_length, ':', 1)::int, "
        f"secs = split_part({song_alias}.song_length, ':', 2)::int"
        f"))"
        )
    # MySQL/MariaDB: 'MM:SS' -> Time -> Sekunden
    return f"TIME_TO_SEC(STR_TO_DATE({song_alias}.song_length, '%i:%s'))"


def artists_agg_left_join(song_alias="s", join_alias="aa"):
    if DB_DIALECT.lower() == "postgres":
        return f"""
        LEFT JOIN (
        SELECT asg.song_id, string_agg(DISTINCT ar.artist_name, ', ') AS artists
        FROM art_songs asg
        JOIN artists ar ON ar.artist_id = asg.artist_id
        GROUP BY asg.song_id
        ) {join_alias} ON {join_alias}.song_id = {song_alias}.song_id
        """
    # MySQL
    return f"""
    LEFT JOIN (
    SELECT asg.song_id, GROUP_CONCAT(DISTINCT ar.artist_name ORDER BY ar.artist_name SEPARATOR ', ') AS artists
    FROM art_songs asg
    JOIN artists ar ON ar.artist_id = asg.artist_id
    GROUP BY asg.song_id
    ) {join_alias} ON {join_alias}.song_id = {song_alias}.song_id
    """


def album_artists_agg_left_join(album_alias="al", join_alias="aa"):
    if DB_DIALECT.lower() == "postgres":
        return f"""
        LEFT JOIN (
            SELECT aa.album_id, string_agg(DISTINCT ar.artist_name, ', ') AS artists
            FROM album_artists aa
            JOIN artists ar ON ar.artist_id = aa.artist_id
            GROUP BY aa.album_id
        ) {join_alias} ON {join_alias}.album_id = {album_alias}.album_id
        """
    # MySQL/MariaDB
    return f"""
    LEFT JOIN (
        SELECT aa.album_id, GROUP_CONCAT(DISTINCT ar.artist_name ORDER BY ar.artist_name SEPARATOR ', ') AS artists
        FROM album_artists aa
        JOIN artists ar ON ar.artist_id = aa.artist_id
        GROUP BY aa.album_id
    ) {join_alias} ON {join_alias}.album_id = {album_alias}.album_id
    """


def day_bucket_expr():
    # DATE() funktioniert in Postgres und MySQL auf einem Timestamp
    return f"DATE({played_at_cast_expr()})"
