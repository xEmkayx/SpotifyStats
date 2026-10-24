# Database
## MYSQL/MariaDB
For this project I used MariaDB on a Raspberry Pi.

# TODO
- add ERD Diagramm of DB
- more about the setup
## Migrationen (Alembic)
Das Schema wird mit Alembic versioniert (`common/db/migrations`). Das Backend führt beim Start
`upgrade head` aus; das Frontend migriert nie selbst. Deploy-Reihenfolge daher: erst Backend, dann Frontend.

- Manuell: `python -m common.db.migrate` (upgrade head)
- Weitere Befehle: `alembic -c common/db/alembic.ini history | current | downgrade <rev>`
- `0001` Baseline (idempotent: legt nur Fehlendes an), `0002` Playlist-Verlauf, `0003` UTC/Millisekunden

Vor jeder Migration ein Backup ziehen: `python -m db.backup_db [zielordner]`
Wiederherstellen: `gunzip -c <datei>.sql.gz | mysql -u <user> -p <datenbank>`

## Einheiten
- `stream_history.played_at`: `DATETIME(3)` in **UTC**, Endzeit des Streams (so liefert Spotify `played_at`).
  `source` = `api` (Import über "zuletzt gehört") oder `export` (Spotify-Datenexport, minutengenau).
  Ortszeit (`DISPLAY_TZ`, Standard Europe/Berlin, inkl. Sommerzeit) berechnet das Frontend per `CONVERT_TZ`;
  dafür müssen die MySQL-Zeitzonentabellen geladen sein (beim offiziellen MySQL-Image der Fall).
- `songs.duration_ms`: Dauer in Millisekunden (das frühere `song_length` "MM:SS" entfällt).
- Alle übrigen Zeitstempel (`checked_at`, `detected_at`, Playlist-Snapshots) ebenfalls UTC.

## Katalog-Abgleich und Versionen
- `songs.isrc / available / relinked_to / checked_at`: Stand laut Spotify (Markt `SPOTIFY_MARKET`, Standard DE)
- `song_relations`: abgeleitete Zuordnung Version -> kanonische Version (`replaced` = Track-Relinking,
  `same_recording` = gleiche ISRC und Dauer ±3 s, `manual`). Wird von `common/catalog/relations.py` neu berechnet.
- `song_relation_overrides`: manuelle Entscheidungen (verbinden bzw. `target_song_id = NULL` = nie automatisch verbinden)
- `song_suggestion_dismissals`: abgelehnte Vorschläge
- `catalog_changes`: Protokoll erkannter Änderungen (Namen, Relinking, Verfügbarkeit)
- `sync_state`: Status der Abgleich-Läufe

`stream_history` wird für Versionen nie umgeschrieben; Statistiken gruppieren über
`COALESCE(song_relations.canonical_song_id, song_id)`.

Abgleich: nächtlich rollierend (`CATALOG_SYNC_HOUR`, Standard 4 Uhr, ganzer Katalog in `CATALOG_ROLLING_DAYS` = 7 Tagen),
vollständig über `GET /db/update/all` am Backend.

## Playlist-Verlauf
- `playlists`: eigene Playlists (Owner = autorisierter User) und `liked` für die Lieblingssongs
- `playlist_snapshots` / `playlist_snapshot_items`: gespeicherte Stände; ein neuer Stand entsteht nur bei Änderungen
  (Inhalt, Reihenfolge, Name, Beschreibung). Die Spotify-`snapshot_id` dient nur der Änderungserkennung.
- Abgleich im Backend alle `PLAYLIST_SYNC_MINUTES` (Standard 60).
- Zurücksetzen/Ersetzen sichert vorher immer den aktuellen Stand und bricht ab, wenn die Playlist seit der Vorschau
  verändert wurde. Playlists mit lokalen Dateien werden nicht neu geschrieben.
