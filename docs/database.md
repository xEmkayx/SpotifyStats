# Database
## MYSQL/MariaDB
For this project I used MariaDB on a Raspberry Pi.

# TODO
- add ERD Diagramm of DB
- more about the setup
## Katalog-Abgleich und Versionen
Schema-Erweiterungen legt `common/db/schema.py` beim Start von Backend und Frontend selbst an (idempotent, nur additiv).

- `songs.isrc / available / relinked_to / duration_ms / checked_at`: Stand laut Spotify (Markt `SPOTIFY_MARKET`, Standard DE)
- `song_relations`: abgeleitete Zuordnung Version -> kanonische Version (`replaced` = Track-Relinking, `same_recording` = gleiche ISRC und Dauer ±3 s, `manual`). Wird von `common/catalog/relations.py` komplett neu berechnet.
- `song_relation_overrides`: manuelle Entscheidungen (verbinden bzw. `target_song_id = NULL` = nie automatisch verbinden)
- `song_suggestion_dismissals`: abgelehnte Vorschläge
- `catalog_changes`: Protokoll erkannter Änderungen (Namen, Relinking, Verfügbarkeit)
- `sync_state`: Status der Abgleich-Läufe

`stream_history` wird nie umgeschrieben; Statistiken gruppieren über `COALESCE(song_relations.canonical_song_id, song_id)`.

Abgleich: nächtlich rollierend (`CATALOG_SYNC_HOUR`, Standard 4 Uhr, ganzer Katalog in `CATALOG_ROLLING_DAYS` = 7 Tagen), vollständig über `GET /db/update/all` am Backend.

Backup: `python -m db.backup_db [zielordner]`
