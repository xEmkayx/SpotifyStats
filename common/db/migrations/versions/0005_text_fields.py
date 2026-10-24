"""Freitextfelder ohne künstliche Längengrenze

Namen, Beschreibungen und Protokollwerte als TEXT statt VARCHAR(500/1000),
auch die Namensspalten der Kerntabellen; der Code schneidet nichts mehr ab.

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-24
"""
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

_UNICODE = "utf8mb4_unicode_ci"
_GENERAL = "utf8mb4_general_ci"

# Tabelle -> [(Spalte, bisherige Länge, Kollation)]; Kollation bleibt wie bisher
_FIELDS = {
    "songs": [("song_name", 500, _UNICODE)],
    "albums": [("album_name", 500, _UNICODE)],
    "artists": [("artist_name", 500, _GENERAL)],
    "playlists": [("name", 500, _UNICODE), ("description", 1000, _UNICODE)],
    "playlist_snapshots": [("name", 500, _UNICODE), ("description", 1000, _UNICODE)],
    "playlist_snapshot_items": [("name", 500, _UNICODE), ("artists", 1000, _UNICODE), ("album", 500, _UNICODE)],
    "catalog_changes": [("old_value", 500, _UNICODE), ("new_value", 500, _UNICODE)],
}


def upgrade():
    for table, columns in _FIELDS.items():
        op.execute(f"ALTER TABLE {table} " + ", ".join(
            f"MODIFY {c} TEXT CHARACTER SET utf8mb4 COLLATE {coll} NULL" for c, _, coll in columns))


def downgrade():
    for table, columns in _FIELDS.items():
        for c, length, _ in columns:
            op.execute(f"UPDATE {table} SET {c} = LEFT({c}, {length})")
        op.execute(f"ALTER TABLE {table} " + ", ".join(
            f"MODIFY {c} VARCHAR({length}) CHARACTER SET utf8mb4 COLLATE {coll} NULL" for c, length, coll in columns))
