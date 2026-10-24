"""
    Versionen desselben Lieds: Gruppen, Vorschläge, Änderungsprotokoll und
    manuelle Entscheidungen (verbinden / trennen / Vorschlag ablehnen).
"""
from collections import defaultdict
from decimal import Decimal

import pandas as pd
from sqlalchemy import text, bindparam

from common.catalog.relations import rebuild_relations, DURATION_TOLERANCE_MS
from frontend_new.config import DISPLAY_TZ
from frontend_new.core.db import engine
from frontend_new.core.extensions import cache
from frontend_new.services.song_search import _escape_like
from frontend_new.services.sql_fragments import artists_of_song_expr

KIND_LABELS = {"replaced": "veraltet", "same_recording": "weiteres Release", "manual": "von dir verbunden"}


def song_group_ids(song_id: str) -> tuple[str, list[str]]:
    # (kanonische ID, alle IDs der Gruppe) für Detailansichten
    with engine.connect() as conn:
        canonical = conn.execute(text("SELECT canonical_song_id FROM song_relations WHERE song_id = :id"),
                                 {"id": song_id}).scalar() or song_id
        members = [r[0] for r in conn.execute(
            text("SELECT song_id FROM song_relations WHERE canonical_song_id = :c"), {"c": canonical})]
    return canonical, [canonical] + members


_GROUPS_BASE = """
    FROM song_relations sr
    JOIN songs c ON c.song_id = sr.canonical_song_id
    LEFT JOIN (SELECT song_id, COUNT(*) AS plays FROM stream_history GROUP BY song_id) p
           ON p.song_id = sr.song_id
"""

_GROUP_SORT = {
    "plays": "total_plays DESC",
    "versions": "versions DESC, total_plays DESC",
    "name": "c.song_name ASC",
}


@cache.memoize(timeout=900)
def version_groups(search: str, kind: str, sort: str, page: int, page_size: int, cache_version: int) -> dict:
    where, params = ["1=1"], {}
    if search:
        params["q"] = f"%{_escape_like(search)}%"
        where.append(f"(c.song_name LIKE :q ESCAPE '!' OR {artists_of_song_expr('c.song_id')} LIKE :q ESCAPE '!')")
    having = ""
    if kind in KIND_LABELS:
        params["kind"] = kind
        having = "HAVING SUM(sr.kind = :kind) > 0"
    order = _GROUP_SORT.get(sort, _GROUP_SORT["plays"])
    canon_plays = "(SELECT COUNT(*) FROM stream_history WHERE song_id = sr.canonical_song_id)"
    sql = f"""
        SELECT sr.canonical_song_id AS canonical, c.song_name,
               COUNT(*) + 1 AS versions,
               COALESCE(SUM(p.plays), 0) + MAX({canon_plays}) AS total_plays
        {_GROUPS_BASE}
        WHERE {" AND ".join(where)}
        GROUP BY sr.canonical_song_id, c.song_name
        {having}
    """
    with engine.connect() as conn:
        total = conn.execute(text(f"SELECT COUNT(*) FROM ({sql}) g"), params).scalar()
        groups = conn.execute(text(f"{sql} ORDER BY {order} LIMIT :limit OFFSET :offset"),
                              {**params, "limit": page_size, "offset": page * page_size}).mappings().all()
        canon_ids = [g["canonical"] for g in groups]
        members = []
        if canon_ids:
            stmt = text(f"""
                SELECT COALESCE(sr.canonical_song_id, s.song_id) AS canonical, s.song_id, s.song_name,
                       COALESCE({artists_of_song_expr('s.song_id')}, '') AS artists,
                       al.album_name, al.album_type, al.release_date, s.available, s.relinked_to,
                       sr.kind, (SELECT COUNT(*) FROM stream_history WHERE song_id = s.song_id) AS plays
                FROM songs s
                LEFT JOIN song_relations sr ON sr.song_id = s.song_id
                LEFT JOIN albums al ON al.album_id = s.album_id
                WHERE s.song_id IN :ids OR sr.canonical_song_id IN :ids
            """).bindparams(bindparam("ids", expanding=True))
            members = [dict(r) for r in conn.execute(stmt, {"ids": canon_ids}).mappings()]
    by_group = defaultdict(list)
    for m in members:
        by_group[m["canonical"]].append(m)
    for ms in by_group.values():
        ms.sort(key=lambda m: (m["kind"] is not None, -m["plays"]))
    return {"total": int(total or 0),
            "groups": [{**dict(g), "members": by_group.get(g["canonical"], [])} for g in groups]}


@cache.memoize(timeout=900)
def suggestions(search: str, cache_version: int) -> list[dict]:
    """
    Unsichere Kandidaten: gleicher Titel (ohne Groß/Klein), gleiche Artists,
    Dauer innerhalb der Toleranz, aber noch nicht in derselben Gruppe
    (z. B. Remaster mit neuer ISRC). Werden nur vorgeschlagen, nie automatisch verbunden.
    """
    with engine.connect() as conn:
        rows = conn.execute(text(f"""
            SELECT s.song_id, s.song_name, s.duration_ms, s.isrc, s.available,
                   COALESCE(sr.canonical_song_id, s.song_id) AS canonical,
                   (SELECT GROUP_CONCAT(asg.artist_id ORDER BY asg.artist_id) FROM art_songs asg
                    WHERE asg.song_id = s.song_id) AS artist_ids,
                   COALESCE({artists_of_song_expr('s.song_id')}, '') AS artists,
                   al.album_name, al.album_type
            FROM songs s
            LEFT JOIN song_relations sr ON sr.song_id = s.song_id
            LEFT JOIN albums al ON al.album_id = s.album_id
            WHERE s.duration_ms IS NOT NULL
        """)).mappings().all()
        plays = dict(conn.execute(text("SELECT song_id, COUNT(*) FROM stream_history GROUP BY song_id")).all())
        dismissed = {(r[0], r[1]) for r in conn.execute(text("SELECT song_a, song_b FROM song_suggestion_dismissals"))}
        pinned = {r[0] for r in conn.execute(text(
            "SELECT song_id FROM song_relation_overrides WHERE target_song_id IS NULL"))}

    buckets = defaultdict(list)
    for r in rows:
        if r["song_id"] not in pinned:
            buckets[((r["song_name"] or "").strip().lower(), r["artist_ids"])].append(r)
    q = (search or "").strip().lower()
    out = []
    for members in buckets.values():
        if len(members) < 2:
            continue
        for i, a in enumerate(members):
            for b in members[i + 1:]:
                if a["canonical"] == b["canonical"] or abs(a["duration_ms"] - b["duration_ms"]) > DURATION_TOLERANCE_MS:
                    continue
                pair = tuple(sorted((a["song_id"], b["song_id"])))
                if pair in dismissed:
                    continue
                if q and q not in (a["song_name"] or "").lower() and q not in (a["artists"] or "").lower():
                    continue
                out.append({"a": dict(a), "b": dict(b), "plays_a": plays.get(a["song_id"], 0),
                            "plays_b": plays.get(b["song_id"], 0)})
    out.sort(key=lambda x: -(x["plays_a"] + x["plays_b"]))
    return out


@cache.memoize(timeout=900)
def catalog_changes(search: str, entity: str, page: int, page_size: int, cache_version: int) -> dict:
    where, params = ["1=1"], {}
    if entity in ("song", "artist", "album"):
        where.append("cc.entity = :entity")
        params["entity"] = entity
    if search:
        where.append("(cc.old_value LIKE :q ESCAPE '!' OR cc.new_value LIKE :q ESCAPE '!' OR cc.entity_id = :raw)")
        params["q"] = f"%{_escape_like(search)}%"
        params["raw"] = search
    sql_where = " AND ".join(where)
    with engine.connect() as conn:
        total = conn.execute(text(f"SELECT COUNT(*) FROM catalog_changes cc WHERE {sql_where}"), params).scalar()
        rows = conn.execute(text(f"""
            SELECT cc.detected_at, cc.entity, cc.entity_id, cc.field, cc.old_value, cc.new_value, cc.source
            FROM catalog_changes cc
            WHERE {sql_where}
            ORDER BY cc.id DESC
            LIMIT :limit OFFSET :offset
        """), {**params, "limit": page_size, "offset": page * page_size}).mappings().all()
    df = pd.DataFrame([dict(r) for r in rows],
                      columns=["detected_at", "entity", "entity_id", "field", "old_value", "new_value", "source"])
    if not df.empty:
        # DB speichert UTC -> Anzeige in Ortszeit
        df["detected_at"] = (pd.to_datetime(df["detected_at"]).dt.tz_localize("UTC").dt.tz_convert(DISPLAY_TZ)
                             .dt.strftime("%Y-%m-%d %H:%M"))
    return {"total": int(total or 0), "rows": df}


def catalog_status() -> dict:
    with engine.connect() as conn:
        counts = conn.execute(text("""
            SELECT COUNT(*) AS songs, SUM(checked_at IS NOT NULL) AS checked, SUM(isrc IS NOT NULL) AS with_isrc,
                   SUM(relinked_to IS NOT NULL) AS relinked, SUM(available = 0 AND relinked_to IS NULL) AS dead,
                   MIN(checked_at) AS oldest_check
            FROM songs
        """)).mappings().first()
        kinds = dict(conn.execute(text("SELECT kind, COUNT(*) FROM song_relations GROUP BY kind")).all())
        groups = conn.execute(text("SELECT COUNT(DISTINCT canonical_song_id) FROM song_relations")).scalar()
        state = {r[0]: (r[1], r[2]) for r in conn.execute(text("SELECT name, value, updated_at FROM sync_state"))}
        overrides = [dict(r) for r in conn.execute(text(f"""
            SELECT o.song_id, o.target_song_id, s.song_name, t.song_name AS target_name, o.created_at
            FROM song_relation_overrides o
            LEFT JOIN songs s ON s.song_id = o.song_id
            LEFT JOIN songs t ON t.song_id = o.target_song_id
            ORDER BY o.created_at DESC
        """)).mappings()]
    return {**{k: (int(v) if isinstance(v, (int, Decimal)) else v) for k, v in dict(counts).items()},
            "kinds": {k: int(v) for k, v in kinds.items()}, "groups": int(groups or 0), "state": state,
            "overrides": overrides}


# --- Manuelle Entscheidungen: schreiben Override und berechnen die Gruppen neu ---

def _song_exists(conn, song_id: str) -> bool:
    return bool(conn.execute(text("SELECT 1 FROM songs WHERE song_id = :id"), {"id": song_id}).scalar())


def merge_songs(song_id: str, target_song_id: str) -> str:
    song_id, target_song_id = (song_id or "").strip(), (target_song_id or "").strip()
    if not song_id or not target_song_id or song_id == target_song_id:
        return "Bitte gib zwei verschiedene Song-IDs ein."
    with engine.begin() as conn:
        for sid in (song_id, target_song_id):
            if not _song_exists(conn, sid):
                return f"Den Song {sid} gibt es hier noch nicht – er muss mindestens einmal gehört worden sein."
        conn.execute(text("""
            INSERT INTO song_relation_overrides (song_id, target_song_id) VALUES (:s, :t)
            ON DUPLICATE KEY UPDATE target_song_id = VALUES(target_song_id), created_at = NOW()
        """), {"s": song_id, "t": target_song_id})
        # Ein vorher "getrenntes" Ziel wieder freigeben, sonst greift die Verbindung nicht
        conn.execute(text("DELETE FROM song_relation_overrides WHERE song_id = :t AND target_song_id IS NULL"),
                     {"t": target_song_id})
        rebuild_relations(conn)
    return "ok"


def split_song(song_id: str) -> str:
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO song_relation_overrides (song_id, target_song_id) VALUES (:s, NULL)
            ON DUPLICATE KEY UPDATE target_song_id = NULL, created_at = NOW()
        """), {"s": song_id})
        rebuild_relations(conn)
    return "ok"


def remove_override(song_id: str) -> str:
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM song_relation_overrides WHERE song_id = :s"), {"s": song_id})
        rebuild_relations(conn)
    return "ok"


def dismiss_suggestion(song_a: str, song_b: str) -> str:
    a, b = sorted((song_a, song_b))
    with engine.begin() as conn:
        conn.execute(text("INSERT IGNORE INTO song_suggestion_dismissals (song_a, song_b) VALUES (:a, :b)"),
                     {"a": a, "b": b})
    return "ok"
