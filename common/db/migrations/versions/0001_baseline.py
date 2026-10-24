"""Baseline: Stand vor Alembic (init-db.sql + Katalog-Erweiterungen)

Idempotent: auf einer bestehenden DB wird nur angelegt, was fehlt (bisher
hat common/db/schema.py diese Erweiterungen beim Start angelegt). Auf einer
leeren DB entsteht das komplette Schema.

Revision ID: 0001
Revises:
Create Date: 2026-10-24
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

_CHARSET = "ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci"

_TABLES = {
    "artists": f"""
        CREATE TABLE artists (
            artist_id VARCHAR(100) NOT NULL,
            artist_name VARCHAR(500) DEFAULT NULL,
            PRIMARY KEY (artist_id)
        ) {_CHARSET}""",
    "albums": f"""
        CREATE TABLE albums (
            album_id VARCHAR(100) NOT NULL,
            album_name VARCHAR(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
            PRIMARY KEY (album_id)
        ) {_CHARSET}""",
    "songs": f"""
        CREATE TABLE songs (
            song_id VARCHAR(100) NOT NULL,
            song_name VARCHAR(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
            album_id VARCHAR(100) NOT NULL,
            song_length VARCHAR(20) NOT NULL,
            PRIMARY KEY (song_id),
            KEY songs_ibfk_1 (album_id),
            CONSTRAINT songs_ibfk_1 FOREIGN KEY (album_id) REFERENCES albums (album_id)
                ON DELETE CASCADE ON UPDATE CASCADE
        ) {_CHARSET}""",
    "stream_history": f"""
        CREATE TABLE stream_history (
            played_at VARCHAR(100) NOT NULL,
            song_id VARCHAR(100) NOT NULL,
            PRIMARY KEY (played_at),
            KEY sh_ibfk_1 (song_id),
            CONSTRAINT sh_ibfk_1 FOREIGN KEY (song_id) REFERENCES songs (song_id)
                ON DELETE CASCADE ON UPDATE CASCADE
        ) {_CHARSET}""",
    "album_artists": f"""
        CREATE TABLE album_artists (
            album_id VARCHAR(100) NOT NULL,
            artist_id VARCHAR(100) NOT NULL,
            PRIMARY KEY (album_id, artist_id),
            KEY album_artists_ibfk_1 (album_id),
            CONSTRAINT album_artists_ibfk_1 FOREIGN KEY (album_id) REFERENCES albums (album_id)
                ON DELETE CASCADE ON UPDATE CASCADE,
            CONSTRAINT album_artists_ibfk_2 FOREIGN KEY (artist_id) REFERENCES artists (artist_id)
                ON DELETE CASCADE ON UPDATE CASCADE
        ) {_CHARSET}""",
    "art_songs": f"""
        CREATE TABLE art_songs (
            song_id VARCHAR(100) NOT NULL,
            artist_id VARCHAR(100) NOT NULL,
            PRIMARY KEY (artist_id, song_id),
            KEY song_id (song_id),
            CONSTRAINT art_songs_ibfk_1 FOREIGN KEY (artist_id) REFERENCES artists (artist_id)
                ON DELETE CASCADE ON UPDATE CASCADE,
            CONSTRAINT art_songs_ibfk_2 FOREIGN KEY (song_id) REFERENCES songs (song_id)
                ON DELETE CASCADE ON UPDATE CASCADE
        ) {_CHARSET}""",
    "song_relations": f"""
        CREATE TABLE song_relations (
            song_id VARCHAR(100) NOT NULL,
            canonical_song_id VARCHAR(100) NOT NULL,
            kind ENUM('replaced', 'same_recording', 'manual') NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (song_id),
            KEY idx_song_relations_canonical (canonical_song_id)
        ) {_CHARSET}""",
    "song_relation_overrides": f"""
        CREATE TABLE song_relation_overrides (
            song_id VARCHAR(100) NOT NULL,
            target_song_id VARCHAR(100) NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (song_id)
        ) {_CHARSET}""",
    "song_suggestion_dismissals": f"""
        CREATE TABLE song_suggestion_dismissals (
            song_a VARCHAR(100) NOT NULL,
            song_b VARCHAR(100) NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (song_a, song_b)
        ) {_CHARSET}""",
    "catalog_changes": f"""
        CREATE TABLE catalog_changes (
            id BIGINT NOT NULL AUTO_INCREMENT,
            entity ENUM('song', 'artist', 'album') NOT NULL,
            entity_id VARCHAR(100) NOT NULL,
            field VARCHAR(40) NOT NULL,
            old_value VARCHAR(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
            new_value VARCHAR(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
            source VARCHAR(20) NOT NULL,
            detected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY idx_catalog_changes_entity (entity, entity_id),
            KEY idx_catalog_changes_detected (detected_at)
        ) {_CHARSET}""",
    "sync_state": f"""
        CREATE TABLE sync_state (
            name VARCHAR(50) NOT NULL,
            value VARCHAR(200) NULL,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (name)
        ) {_CHARSET}""",
}

_COLUMNS = [
    ("songs", "isrc", "ALTER TABLE songs ADD COLUMN isrc VARCHAR(20) NULL"),
    ("songs", "available", "ALTER TABLE songs ADD COLUMN available TINYINT NULL"),
    ("songs", "relinked_to", "ALTER TABLE songs ADD COLUMN relinked_to VARCHAR(100) NULL"),
    ("songs", "duration_ms", "ALTER TABLE songs ADD COLUMN duration_ms INT NULL"),
    ("songs", "checked_at", "ALTER TABLE songs ADD COLUMN checked_at DATETIME NULL"),
    ("albums", "album_type", "ALTER TABLE albums ADD COLUMN album_type VARCHAR(20) NULL"),
    ("albums", "release_date", "ALTER TABLE albums ADD COLUMN release_date VARCHAR(10) NULL"),
]

_INDEXES = [
    ("songs", "idx_songs_isrc", "CREATE INDEX idx_songs_isrc ON songs (isrc)"),
    ("songs", "idx_songs_checked_at", "CREATE INDEX idx_songs_checked_at ON songs (checked_at)"),
]


def upgrade():
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    for name, ddl in _TABLES.items():  # Reihenfolge berücksichtigt Fremdschlüssel
        if name not in tables:
            op.execute(ddl)
    inspector = sa.inspect(op.get_bind())
    for table, column, ddl in _COLUMNS:
        if column not in {c["name"] for c in inspector.get_columns(table)}:
            op.execute(ddl)
    for table, index, ddl in _INDEXES:
        if index not in {i["name"] for i in inspector.get_indexes(table)}:
            op.execute(ddl)


def downgrade():
    # Baseline wird nicht zurückgerollt (würde die Kerntabellen löschen)
    raise NotImplementedError("Baseline kann nicht zurückgerollt werden")
