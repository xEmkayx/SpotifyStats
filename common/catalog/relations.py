"""
    Gruppiert Songs, die dasselbe Lied abbilden, und berechnet song_relations neu.

    Automatisch verbunden wird nur, was eindeutig ist:
      - Track-Relinking: Spotify leitet die alte ID auf eine neue um (songs.relinked_to)
      - gleiche ISRC UND Dauer innerhalb von DURATION_TOLERANCE_MS
        (Single + Album, Compilation, Deluxe ... derselben Aufnahme)
    Nur gleicher Titel reicht nie (Intro/Outro, Live, Remaster mit eigener ISRC).
    Manuelle Entscheidungen aus song_relation_overrides haben Vorrang.
"""
import logging
from collections import defaultdict

from sqlalchemy import text

DURATION_TOLERANCE_MS = 3000
_ALBUM_TYPE_RANK = {"album": 0, "single": 1, "compilation": 2}


class _UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        self.parent[self.find(a)] = self.find(b)


def rebuild_relations(conn) -> dict:
    songs = {r.song_id: r for r in conn.execute(text("""
        SELECT s.song_id, s.isrc, s.duration_ms, s.available, s.relinked_to, al.album_type,
               COALESCE(p.plays, 0) AS plays
        FROM songs s
        LEFT JOIN albums al ON al.album_id = s.album_id
        LEFT JOIN (SELECT song_id, COUNT(*) AS plays FROM stream_history GROUP BY song_id) p
               ON p.song_id = s.song_id
    """))}
    overrides = {r[0]: r[1] for r in conn.execute(text(
        "SELECT song_id, target_song_id FROM song_relation_overrides"))}
    pinned_separate = {sid for sid, target in overrides.items() if target is None}

    uf = _UnionFind()
    for sid, s in songs.items():
        if s.relinked_to and s.relinked_to in songs and sid not in pinned_separate \
                and s.relinked_to not in pinned_separate:
            uf.union(sid, s.relinked_to)

    by_isrc = defaultdict(list)
    for sid, s in songs.items():
        if s.isrc and s.duration_ms and sid not in pinned_separate:
            by_isrc[s.isrc].append(s)
    for members in by_isrc.values():
        members.sort(key=lambda m: m.duration_ms)
        for prev, cur in zip(members, members[1:]):
            if cur.duration_ms - prev.duration_ms <= DURATION_TOLERANCE_MS:
                uf.union(prev.song_id, cur.song_id)

    for sid, target in overrides.items():
        if target and sid in songs and target in songs:
            uf.union(sid, target)

    groups = defaultdict(list)
    for sid in songs:
        groups[uf.find(sid)].append(sid)

    def canonical_rank(sid):
        s = songs[sid]
        # abspielbar & nicht umgeleitet > meiste Streams > Album vor Single/Compilation
        playable = 0 if (s.available != 0 and not s.relinked_to) else 1
        return playable, -s.plays, _ALBUM_TYPE_RANK.get(s.album_type, 3), sid

    rows = []
    counts = defaultdict(int)
    for members in groups.values():
        if len(members) < 2:
            continue
        canonical = min(members, key=canonical_rank)
        for sid in members:
            if sid == canonical:
                continue
            if overrides.get(sid):
                kind = "manual"
            elif songs[sid].relinked_to:
                kind = "replaced"
            else:
                kind = "same_recording"
            counts[kind] += 1
            rows.append({"song_id": sid, "canonical": canonical, "kind": kind})

    conn.execute(text("DELETE FROM song_relations"))
    if rows:
        conn.execute(text("""
            INSERT INTO song_relations (song_id, canonical_song_id, kind) VALUES (:song_id, :canonical, :kind)
        """), rows)
    result = {"groups": sum(1 for m in groups.values() if len(m) > 1), **counts}
    logging.info(f"Song-Relationen neu berechnet: {result}")
    return result
