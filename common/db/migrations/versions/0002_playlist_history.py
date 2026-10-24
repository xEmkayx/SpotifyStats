"""Playlist-Verlauf: eigene Playlists und Lieblingssongs als Snapshots

Ein Snapshot entsteht nur, wenn sich Inhalt, Reihenfolge, Name oder
Beschreibung geändert haben. Zeitstempel sind UTC.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-24
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

# IDs wie in den bestehenden Tabellen (general_ci, sonst Kollationskonflikt bei Joins), Namen unicode_ci
_CHARSET = "ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci"
_TEXT = "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"


def upgrade():
    # playlist_id 'liked' steht für die Lieblingssongs
    op.execute(f"""
        CREATE TABLE playlists (
            playlist_id VARCHAR(100) NOT NULL,
            name VARCHAR(500) {_TEXT} NULL,
            description VARCHAR(1000) {_TEXT} NULL,
            owner_id VARCHAR(100) NULL,
            is_public TINYINT NULL,
            collaborative TINYINT NULL,
            image_url VARCHAR(500) NULL,
            spotify_snapshot_id VARCHAR(100) NULL,
            track_count INT NULL,
            first_seen_at DATETIME(3) NOT NULL,
            last_synced_at DATETIME(3) NULL,
            last_changed_at DATETIME(3) NULL,
            deleted_at DATETIME(3) NULL,
            PRIMARY KEY (playlist_id)
        ) {_CHARSET}
    """)
    op.execute(f"""
        CREATE TABLE playlist_snapshots (
            id BIGINT NOT NULL AUTO_INCREMENT,
            playlist_id VARCHAR(100) NOT NULL,
            spotify_snapshot_id VARCHAR(100) NULL,
            name VARCHAR(500) {_TEXT} NULL,
            description VARCHAR(1000) {_TEXT} NULL,
            track_count INT NOT NULL,
            content_hash CHAR(40) NOT NULL,
            reason VARCHAR(20) NOT NULL,
            taken_at DATETIME(3) NOT NULL,
            PRIMARY KEY (id),
            KEY idx_playlist_snapshots_playlist (playlist_id, taken_at),
            CONSTRAINT fk_playlist_snapshots_playlist FOREIGN KEY (playlist_id)
                REFERENCES playlists (playlist_id) ON DELETE CASCADE
        ) {_CHARSET}
    """)
    op.execute(f"""
        CREATE TABLE playlist_snapshot_items (
            snapshot_id BIGINT NOT NULL,
            position INT NOT NULL,
            uri VARCHAR(200) NULL,
            track_id VARCHAR(100) NULL,
            playable_id VARCHAR(100) NULL,
            name VARCHAR(500) {_TEXT} NULL,
            artists VARCHAR(1000) {_TEXT} NULL,
            album VARCHAR(500) {_TEXT} NULL,
            duration_ms INT NULL,
            added_at DATETIME(3) NULL,
            added_by VARCHAR(100) NULL,
            is_local TINYINT NOT NULL DEFAULT 0,
            PRIMARY KEY (snapshot_id, position),
            KEY idx_playlist_snapshot_items_track (track_id),
            CONSTRAINT fk_playlist_snapshot_items_snapshot FOREIGN KEY (snapshot_id)
                REFERENCES playlist_snapshots (id) ON DELETE CASCADE
        ) {_CHARSET}
    """)


def downgrade():
    op.execute("DROP TABLE playlist_snapshot_items")
    op.execute("DROP TABLE playlist_snapshots")
    op.execute("DROP TABLE playlists")
