from datetime import date, timedelta

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


def day_bucket_expr(alias="sh"):
    # played_at beginnt immer mit "YYYY-MM-DD" -> kein Parsen pro Zeile nötig
    return f"LEFT({alias}.played_at, 10)"


def hour_expr(alias="sh"):
    # "YYYY-MM-DD HH:..." -> HH
    if DB_DIALECT.lower() == "postgres":
        return f"CAST(SUBSTRING({alias}.played_at, 12, 2) AS INTEGER)"
    return f"CAST(SUBSTRING({alias}.played_at, 12, 2) AS UNSIGNED)"


def weekday_expr(alias="sh"):
    # 0 = Montag .. 6 = Sonntag
    if DB_DIALECT.lower() == "postgres":
        return f"(EXTRACT(ISODOW FROM CAST(LEFT({alias}.played_at, 10) AS DATE)) - 1)"
    return f"WEEKDAY(LEFT({alias}.played_at, 10))"


def played_at_range_expr(alias="sh"):
    # played_at ist ein varchar mit ISO-Präfix ("YYYY-MM-DD HH:MM[:SS[.ffffff]]"),
    # lexikografisch also gleich chronologisch. Der direkte Vergleich nutzt den
    # PK-Index statt STR_TO_DATE für jede Zeile auszuwerten.
    return f"{alias}.played_at >= :start_dt AND {alias}.played_at < :end_dt"


def range_params(start, end) -> dict:
    # Akzeptiert "YYYY-MM-DD", "YYYY-MM-DD HH:MM" oder date; Ende ist inklusive des ganzen Tages
    start_day = str(start)[:10]
    end_excl = date.fromisoformat(str(end)[:10]) + timedelta(days=1)
    return {"start_dt": start_day, "end_dt": end_excl.isoformat()}


def artists_of_song_expr(song_col="s.song_id"):
    # Korrelierte Subquery: nur sinnvoll, nachdem auf Top-N limitiert wurde
    if DB_DIALECT.lower() == "postgres":
        return (f"(SELECT string_agg(DISTINCT ar.artist_name, ', ') FROM art_songs asg "
                f"JOIN artists ar ON ar.artist_id = asg.artist_id WHERE asg.song_id = {song_col})")
    return (f"(SELECT GROUP_CONCAT(DISTINCT ar.artist_name ORDER BY ar.artist_name SEPARATOR ', ') "
            f"FROM art_songs asg JOIN artists ar ON ar.artist_id = asg.artist_id WHERE asg.song_id = {song_col})")


def artists_of_album_expr(album_col="al.album_id"):
    if DB_DIALECT.lower() == "postgres":
        return (f"(SELECT string_agg(DISTINCT ar.artist_name, ', ') FROM album_artists aa "
                f"JOIN artists ar ON ar.artist_id = aa.artist_id WHERE aa.album_id = {album_col})")
    return (f"(SELECT GROUP_CONCAT(DISTINCT ar.artist_name ORDER BY ar.artist_name SEPARATOR ', ') "
            f"FROM album_artists aa JOIN artists ar ON ar.artist_id = aa.artist_id WHERE aa.album_id = {album_col})")


def plays_per_song_sql(extra_where: str = "", extra_join: str = "") -> str:
    # Plays + Sekunden pro Song im Zeitraum (played_at ist PK -> COUNT(*) ohne DISTINCT)
    where = f"{played_at_range_expr()}" + (f" AND ({extra_where})" if extra_where else "")
    return f"""
    SELECT sh.song_id, COUNT(*) AS plays, COUNT(*) * MAX({length_seconds_expr("s")}) AS seconds_total
    FROM stream_history sh
    JOIN songs s ON s.song_id = sh.song_id
    {extra_join}
    WHERE {where}
    GROUP BY sh.song_id
    """


def order_column(metric: str) -> str:
    # Nur feste Spaltennamen in ORDER BY (kein User-Input im SQL)
    return "seconds_total" if (metric or "plays").lower() == "minutes" else "plays"
