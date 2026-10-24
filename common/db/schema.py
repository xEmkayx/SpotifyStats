"""
    Idempotente Schema-Erweiterungen. Wird beim Start von Backend und Frontend
    ausgeführt; bereits vorhandene Spalten/Tabellen werden übersprungen.
    Alle Änderungen sind additiv (nullable Spalten, neue Tabellen), ältere
    Versionen von Backend/Frontend laufen damit weiter.
"""
import logging

from sqlalchemy import text

from common.db.engine import engine

# (Tabelle, Spalte, DDL)
_COLUMNS = [
    ("songs", "isrc", "ALTER TABLE songs ADD COLUMN isrc VARCHAR(20) NULL"),
    # Ist diese ID selbst in DE abspielbar? (0 = tot oder durch Relinking ersetzt)
    ("songs", "available", "ALTER TABLE songs ADD COLUMN available TINYINT NULL"),
    # Spotify leitet diese ID auf eine andere um (Track-Relinking)
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

_TABLES = {
    # Abgeleitet (wird von common.catalog.relations komplett neu berechnet):
    # jede song_id zeigt auf ihre kanonische Version. Fehlt eine Zeile, ist der
    # Song seine eigene kanonische Version.
    # kind: replaced (Relinking), same_recording (gleiche ISRC + Dauer), manual (von Hand verbunden)
    "song_relations": """
        CREATE TABLE song_relations (
            song_id VARCHAR(100) NOT NULL,
            canonical_song_id VARCHAR(100) NOT NULL,
            kind ENUM('replaced', 'same_recording', 'manual') NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (song_id),
            KEY idx_song_relations_canonical (canonical_song_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """,
    # Manuelle Entscheidungen, überleben jede Neuberechnung.
    # target_song_id = andere ID -> in deren Gruppe aufnehmen; NULL -> nie automatisch verbinden
    "song_relation_overrides": """
        CREATE TABLE song_relation_overrides (
            song_id VARCHAR(100) NOT NULL,
            target_song_id VARCHAR(100) NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (song_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """,
    # Abgelehnte Vorschläge (Paar soll nicht mehr vorgeschlagen werden), song_a < song_b
    "song_suggestion_dismissals": """
        CREATE TABLE song_suggestion_dismissals (
            song_a VARCHAR(100) NOT NULL,
            song_b VARCHAR(100) NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (song_a, song_b)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """,
    "catalog_changes": """
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """,
    "sync_state": """
        CREATE TABLE sync_state (
            name VARCHAR(50) NOT NULL,
            value VARCHAR(200) NULL,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """,
}

# MySQL-Fehlercodes für "existiert schon" (Rennen zwischen Backend- und Frontend-Start)
_ALREADY_EXISTS = {1050, 1060, 1061}


def _execute_ddl(conn, ddl: str):
    try:
        conn.execute(text(ddl))
    except Exception as e:
        code = getattr(getattr(e, "orig", None), "args", [None])[0]
        if code not in _ALREADY_EXISTS:
            raise


def ensure_schema():
    with engine.begin() as conn:
        tables = {r[0] for r in conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE()"))}
        columns = {(r[0], r[1]) for r in conn.execute(text(
            "SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = DATABASE()"))}
        indexes = {(r[0], r[1]) for r in conn.execute(text(
            "SELECT table_name, index_name FROM information_schema.statistics WHERE table_schema = DATABASE()"))}
    for name, ddl in _TABLES.items():
        if name not in tables:
            with engine.begin() as conn:
                _execute_ddl(conn, ddl)
            logging.info(f"Schema: Tabelle {name} angelegt")
    for table, column, ddl in _COLUMNS:
        if (table, column) not in columns:
            with engine.begin() as conn:
                _execute_ddl(conn, ddl)
            logging.info(f"Schema: Spalte {table}.{column} angelegt")
    for table, index, ddl in _INDEXES:
        if (table, index) not in indexes:
            with engine.begin() as conn:
                _execute_ddl(conn, ddl)
            logging.info(f"Schema: Index {index} angelegt")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ensure_schema()
