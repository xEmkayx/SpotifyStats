"""Spotify-snapshot_id ohne künstliche Längengrenze

Die snapshot_id ist für Spotify eine undurchsichtige Zeichenkette; VARCHAR(100) war willkürlich.

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-25
"""
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE playlists MODIFY spotify_snapshot_id TEXT NULL")
    op.execute("ALTER TABLE playlist_snapshots MODIFY spotify_snapshot_id TEXT NULL")


def downgrade():
    op.execute("ALTER TABLE playlist_snapshots MODIFY spotify_snapshot_id VARCHAR(100) NULL")
    op.execute("ALTER TABLE playlists MODIFY spotify_snapshot_id VARCHAR(100) NULL")
