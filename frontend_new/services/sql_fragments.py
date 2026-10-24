import re
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from frontend_new.config import DB_DIALECT, DISPLAY_TZ

# played_at ist DATETIME(3) in UTC. Auswertungen nach Tag/Stunde/Wochentag laufen in Ortszeit
# (inkl. Sommerzeit); der Zeitzonenname wird als Literal eingesetzt, daher streng geprüft.
if not re.fullmatch(r"[A-Za-z_]+(/[A-Za-z0-9_+\-]+)*", DISPLAY_TZ):
    raise ValueError(f"Ungültige DISPLAY_TZ: {DISPLAY_TZ!r}")
_TZ = ZoneInfo(DISPLAY_TZ)


def local_time_expr(alias="sh"):
    if DB_DIALECT.lower() == "postgres":
        return f"({alias}.played_at AT TIME ZONE 'UTC' AT TIME ZONE '{DISPLAY_TZ}')"
    return f"CONVERT_TZ({alias}.played_at, 'UTC', '{DISPLAY_TZ}')"


def played_at_cast_expr():
    # Zeitpunkt in Ortszeit (für Detailauswertungen in pandas)
    return local_time_expr()


def length_seconds_expr(song_alias="s"):
    return f"({song_alias}.duration_ms / 1000)"


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
    # Kalendertag in Ortszeit als 'YYYY-MM-DD'
    if DB_DIALECT.lower() == "postgres":
        return f"to_char({local_time_expr(alias)}, 'YYYY-MM-DD')"
    return f"DATE_FORMAT({local_time_expr(alias)}, '%Y-%m-%d')"


def hour_expr(alias="sh"):
    if DB_DIALECT.lower() == "postgres":
        return f"CAST(EXTRACT(HOUR FROM {local_time_expr(alias)}) AS INTEGER)"
    return f"HOUR({local_time_expr(alias)})"


def weekday_expr(alias="sh"):
    # 0 = Montag .. 6 = Sonntag
    if DB_DIALECT.lower() == "postgres":
        return f"(EXTRACT(ISODOW FROM {local_time_expr(alias)}) - 1)"
    return f"WEEKDAY({local_time_expr(alias)})"


def played_at_range_expr(alias="sh"):
    # Vergleich direkt auf der UTC-Spalte -> nutzt den PK-Index
    return f"{alias}.played_at >= :start_dt AND {alias}.played_at < :end_dt"


def _local_midnight_utc(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, tzinfo=_TZ).astimezone(timezone.utc).replace(tzinfo=None)


def range_params(start, end) -> dict:
    # Akzeptiert "YYYY-MM-DD", "YYYY-MM-DD HH:MM" oder date. Gemeint sind ganze Kalendertage in Ortszeit;
    # die Grenzen werden nach UTC umgerechnet (Ende exklusiv: Mitternacht nach dem Endtag).
    start_day = date.fromisoformat(str(start)[:10])
    end_day = date.fromisoformat(str(end)[:10]) + timedelta(days=1)
    return {"start_dt": _local_midnight_utc(start_day), "end_dt": _local_midnight_utc(end_day)}


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


def canonical_song_expr(alias="sh"):
    # Versionen desselben Lieds (ersetzte Releases, gleiche Aufnahme) zählen für die kanonische ID
    return f"COALESCE(sr.canonical_song_id, {alias}.song_id)"


def canonical_join(alias="sh"):
    return f"LEFT JOIN song_relations sr ON sr.song_id = {alias}.song_id"


def plays_per_song_sql(extra_where: str = "", extra_join: str = "") -> str:
    # Plays + Sekunden pro (kanonischem) Song im Zeitraum (played_at ist PK -> COUNT(*) ohne DISTINCT).
    # s ist die tatsächlich gespielte Version (Filter, Länge), song_id im Ergebnis die kanonische.
    where = f"{played_at_range_expr()}" + (f" AND ({extra_where})" if extra_where else "")
    return f"""
    SELECT {canonical_song_expr()} AS song_id, COUNT(*) AS plays, SUM({length_seconds_expr("s")}) AS seconds_total
    FROM stream_history sh
    JOIN songs s ON s.song_id = sh.song_id
    {canonical_join()}
    {extra_join}
    WHERE {where}
    GROUP BY {canonical_song_expr()}
    """


def order_column(metric: str) -> str:
    # Nur feste Spaltennamen in ORDER BY (kein User-Input im SQL)
    return "seconds_total" if (metric or "plays").lower() == "minutes" else "plays"
