"""Playlist-Einträge: uri als TEXT

URIs lokaler Dateien enthalten Artist, Album und Titel URL-kodiert
(spotify:local:...) und sprengen VARCHAR(200).

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-24
"""
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE playlist_snapshot_items MODIFY uri TEXT NULL")


def downgrade():
    op.execute("UPDATE playlist_snapshot_items SET uri = LEFT(uri, 200)")
    op.execute("ALTER TABLE playlist_snapshot_items MODIFY uri VARCHAR(200) NULL")
