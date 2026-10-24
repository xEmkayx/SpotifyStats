"""Einheitliche Einheiten: played_at als DATETIME(3) in UTC, Dauer nur noch in ms

stream_history.played_at war ein varchar in zwei Varianten, beide = Endzeit des Streams:
  - API-Import ("YYYY-MM-DD HH:MM:SS[.ffffff]"): UTC + pauschal 1 Stunde
  - Spotify-Datenexport ("YYYY-MM-DD HH:MM", endTime): UTC, minutengenau
Danach: played_at DATETIME(3) in UTC (Primärschlüssel), source = 'api' | 'export'.
Anzeige in Ortszeit (inkl. Sommerzeit) übernimmt das Frontend per CONVERT_TZ.

songs.song_length ("MM:SS") entfällt; songs.duration_ms ist Pflicht.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-24
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

API_OFFSET_HOURS = 1


def _scalar(sql: str):
    return op.get_bind().execute(sa.text(sql)).scalar()


def upgrade():
    # Ortszeit-Auswertungen brauchen die Zeitzonen-Tabellen von MySQL
    if _scalar("SELECT CONVERT_TZ('2026-07-01 12:00:00', 'UTC', 'Europe/Berlin')") is None:
        raise RuntimeError("MySQL-Zeitzonentabellen fehlen (CONVERT_TZ liefert NULL). "
                           "Bitte mit mysql_tzinfo_to_sql laden und Migration erneut starten.")

    # --- stream_history ---
    op.execute("""
        ALTER TABLE stream_history
            ADD COLUMN played_at_utc DATETIME(3) NULL,
            ADD COLUMN source ENUM('api', 'export') NOT NULL DEFAULT 'api'
    """)
    op.execute(f"""
        UPDATE stream_history SET
            played_at_utc = CASE
                WHEN CHAR_LENGTH(played_at) = 16 THEN STR_TO_DATE(played_at, '%Y-%m-%d %H:%i')
                ELSE STR_TO_DATE(played_at, '%Y-%m-%d %H:%i:%s.%f') - INTERVAL {API_OFFSET_HOURS} HOUR
            END,
            source = IF(CHAR_LENGTH(played_at) = 16, 'export', 'api')
    """)
    missing = _scalar("SELECT COUNT(*) FROM stream_history WHERE played_at_utc IS NULL")
    if missing:
        raise RuntimeError(f"{missing} Zeitstempel ließen sich nicht umrechnen; Migration abgebrochen.")
    dupes = _scalar("SELECT COUNT(*) FROM (SELECT played_at_utc FROM stream_history "
                    "GROUP BY played_at_utc HAVING COUNT(*) > 1) d")
    if dupes:
        raise RuntimeError(f"{dupes} Zeitstempel wären nach der Umrechnung doppelt; Migration abgebrochen.")
    op.execute("""
        ALTER TABLE stream_history
            DROP PRIMARY KEY,
            DROP COLUMN played_at,
            RENAME COLUMN played_at_utc TO played_at
    """)
    op.execute("""
        ALTER TABLE stream_history
            MODIFY played_at DATETIME(3) NOT NULL FIRST,
            ADD PRIMARY KEY (played_at)
    """)

    # --- songs: Dauer nur noch in Millisekunden ---
    op.execute("""
        UPDATE songs SET duration_ms = TIME_TO_SEC(STR_TO_DATE(song_length, '%i:%s')) * 1000
        WHERE duration_ms IS NULL
    """)
    op.execute("UPDATE songs SET duration_ms = 0 WHERE duration_ms IS NULL")
    op.execute("ALTER TABLE songs MODIFY duration_ms INT NOT NULL, DROP COLUMN song_length")


def downgrade():
    op.execute("ALTER TABLE songs ADD COLUMN song_length VARCHAR(20) NOT NULL DEFAULT '' AFTER album_id")
    op.execute("""
        UPDATE songs SET song_length = CONCAT(LPAD(FLOOR(duration_ms / 60000), 2, '0'), ':',
                                              LPAD(MOD(FLOOR(duration_ms / 1000), 60), 2, '0'))
    """)
    op.execute("ALTER TABLE songs MODIFY duration_ms INT NULL")

    op.execute("ALTER TABLE stream_history ADD COLUMN played_at_str VARCHAR(100) NULL")
    op.execute(f"""
        UPDATE stream_history SET played_at_str = CASE
            WHEN source = 'export' THEN DATE_FORMAT(played_at, '%Y-%m-%d %H:%i')
            ELSE DATE_FORMAT(played_at + INTERVAL {API_OFFSET_HOURS} HOUR, '%Y-%m-%d %H:%i:%s.%f')
        END
    """)
    op.execute("""
        ALTER TABLE stream_history
            DROP PRIMARY KEY,
            DROP COLUMN played_at,
            DROP COLUMN source,
            RENAME COLUMN played_at_str TO played_at
    """)
    op.execute("ALTER TABLE stream_history MODIFY played_at VARCHAR(100) NOT NULL FIRST, ADD PRIMARY KEY (played_at)")
