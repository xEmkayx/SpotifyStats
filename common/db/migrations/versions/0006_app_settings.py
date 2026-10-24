"""Einstellungen, die in der Oberfläche geändert werden (z. B. automatischer Austausch)

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-24
"""
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE app_settings (
            name VARCHAR(100) NOT NULL,
            value TEXT NULL,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)


def downgrade():
    op.execute("DROP TABLE app_settings")
