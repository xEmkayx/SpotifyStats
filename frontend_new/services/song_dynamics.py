from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional
import numpy as np
import pandas as pd
from sqlalchemy import text

from frontend_new.core.db import engine
from frontend_new.core.extensions import cache
from frontend_new.services.spotify_images import track_images, album_images
from frontend_new.services.sql_fragments import played_at_cast_expr

# Hilfsfunktionen

def _parse_song_length_to_sec(s: Optional[str]) -> int:
    # Erwartet "MM:SS" oder "HH:MM:SS"
    if not s:
        return 0
    parts = s.split(":")
    try:
        if len(parts) == 2:
            m, sec = int(parts[0]), int(parts[1])
            return m * 60 + sec
        if len(parts) == 3:
            h, m, sec = int(parts[0]), int(parts[1]), int(parts[2])
            return h * 3600 + m * 60 + sec
    except Exception:
        return 0
    return 0


@dataclass
class SongMeta:
    song_id: str
    song_name: str
    album_name: Optional[str]
    artists: str
    song_length_sec: int
    image_url: str = ""
    album_id: Optional[str] = None


@cache.memoize(timeout=1800)
def song_meta(song_id: str) -> SongMeta | None:
    sql = """
    SELECT
        s.song_id,
        s.song_name,
        s.album_id,                  -- NEU
        al.album_name,
        COALESCE(aa.artists, '') AS artists,
        s.song_length
    FROM songs s
    LEFT JOIN albums al ON al.album_id = s.album_id
    LEFT JOIN (
        SELECT asg.song_id,
               GROUP_CONCAT(DISTINCT ar.artist_name ORDER BY ar.artist_name SEPARATOR ', ') AS artists
        FROM art_songs asg
        JOIN artists ar ON ar.artist_id = asg.artist_id
        GROUP BY asg.song_id
    ) aa ON aa.song_id = s.song_id
    WHERE s.song_id = :song_id
    """
    with engine.begin() as conn:
        row = conn.execute(text(sql), {"song_id": song_id}).mappings().first()
    if not row:
        return None

    length_sec = _parse_song_length_to_sec(row.get("song_length"))

    # Bild laden: zuerst Track, dann Album (Fallback)
    img_url = ""
    try:
        tmap = track_images((row["song_id"],))
        img_url = (tmap.get(row["song_id"]) or "").strip()
        if not img_url and row.get("album_id"):
            amap = album_images((row["album_id"],))
            img_url = (amap.get(row["album_id"]) or "").strip()
    except Exception:
        # Bildservice optional – Karte funktioniert auch ohne Bild
        img_url = ""

    return SongMeta(
        song_id=row["song_id"],
        song_name=row.get("song_name") or "",
        album_name=row.get("album_name"),
        artists=row.get("artists") or "",
        song_length_sec=length_sec,
        image_url=img_url,
        album_id=row.get("album_id")
    )


def _fetch_timestamps(song_id: str) -> pd.Series:
    # Roh-Timestamps (als echte DATETIME) aus DB ziehen und als Pandas Series zurückgeben
    cast_expr = played_at_cast_expr()  # nutzt Sekunden + Mikrosekunden
    sql = f"""
    SELECT {cast_expr} AS ts
    FROM stream_history sh
    WHERE sh.song_id = :song_id
    ORDER BY ts
    """
    with engine.begin() as conn:
        rows = conn.execute(text(sql), {"song_id": song_id}).fetchall()
    if not rows:
        return pd.Series([], dtype="datetime64[ns]", name="ts")
    ts = pd.to_datetime([r[0] for r in rows])
    # WICHTIG: Als Series zurückgeben, nicht als DatetimeIndex
    return pd.Series(ts, name="ts")


def _apply_date_range(ts: pd.Series, date_start: Optional[datetime], date_end: Optional[datetime]) -> pd.Series:
    if ts.empty:
        return ts
    mask = pd.Series([True] * len(ts))
    if date_start:
        mask &= (ts >= pd.to_datetime(date_start))
    if date_end:
        mask &= (ts <= pd.to_datetime(date_end))
    return ts[mask]


def _distinct_days(ts: pd.Series) -> pd.Series:
    if ts.empty:
        return pd.Series([], dtype="datetime64[ns]")
    return pd.to_datetime(ts.dt.date)


def _longest_streak_days(days: pd.Series) -> int:
    # längste Serie aufeinanderfolgender Kalendertage
    if days.empty:
        return 0
    d_sorted = pd.to_datetime(pd.Series(pd.unique(days))).sort_values()
    diffs = d_sorted.diff().dt.days.fillna(1)
    # neue Sequenz beginnt, wenn diff != 1
    run_lengths = []
    run_len = 0
    prev = None
    for d in d_sorted:
        if prev is None or (d - prev).days == 1:
            run_len += 1
        else:
            run_lengths.append(run_len)
            run_len = 1
        prev = d
    run_lengths.append(run_len)
    return int(max(run_lengths) if run_lengths else 0)


def _gaps_days(ts: pd.Series) -> np.ndarray:
    # Abstände zwischen aufeinanderfolgenden Plays in Tagen (float)
    if len(ts) < 2:
        return np.array([])
    diffs = ts.diff().iloc[1:]
    return diffs.dt.total_seconds().to_numpy() / 86400.0


def _days_to_50pct(ts: pd.Series) -> Optional[int]:
    # Tage bis 50% der Gesamtplays erreicht sind (ab erstem Play)
    if ts.empty:
        return None
    total = len(ts)
    half = np.ceil(total * 0.5)
    # erstes Index, an dem kumulativ >= half
    idx = int(half) - 1
    ts_sorted = ts.sort_values().reset_index(drop=True)
    first = ts_sorted.iloc[0]
    target = ts_sorted.iloc[idx]
    return (target.date() - first.date()).days


@cache.memoize(timeout=1800)
def song_overview(song_id: str, date_start_iso: Optional[str], date_end_iso: Optional[str], cache_ver: int = 0) -> dict:
    meta = song_meta(song_id)
    if not meta:
        return {"exists": False}

    ts = _fetch_timestamps(song_id)
    date_start = pd.to_datetime(date_start_iso) if date_start_iso else None
    date_end = pd.to_datetime(date_end_iso) if date_end_iso else None
    ts = _apply_date_range(ts, date_start, date_end)

    total_plays = int(len(ts))
    if total_plays == 0:
        return {
            "exists": True,
            "meta": meta.__dict__,
            "total_plays": 0,
            "seconds_total": 0,
            "first_play": None,
            "last_play": None,
            "unique_days": 0,
            "longest_streak_days": 0,
            "median_gap_days": None,
            "mean_gap_days": None,
            "current_silence_days": None,
            "days_to_50pct": None
        }

    seconds_total = int(total_plays * meta.song_length_sec)
    first_play = ts.iloc[0]
    last_play = ts.iloc[-1]
    days = _distinct_days(ts)

    gaps = _gaps_days(ts)
    median_gap = float(np.median(gaps)) if gaps.size else None
    mean_gap = float(np.mean(gaps)) if gaps.size else None

    # Silence: von letztem Play bis Ende der Auswahl (oder heute, falls kein Enddatum)
    ref_end = date_end if date_end else pd.Timestamp(datetime.utcnow())
    current_silence = (ref_end.normalize() - last_play.normalize()).days
    current_silence = max(current_silence, 0)

    return {
        "exists": True,
        "meta": meta.__dict__,
        "total_plays": total_plays,
        "seconds_total": seconds_total,
        "first_play": first_play.isoformat(),
        "last_play": last_play.isoformat(),
        "unique_days": int(days.nunique()),
        "longest_streak_days": _longest_streak_days(days),
        "median_gap_days": round(median_gap, 2) if median_gap is not None else None,
        "mean_gap_days": round(mean_gap, 2) if mean_gap is not None else None,
        "current_silence_days": int(current_silence),
        "days_to_50pct": _days_to_50pct(ts),
    }


@cache.memoize(timeout=1800)
def song_weekly_counts(song_id: str, date_start_iso: Optional[str], date_end_iso: Optional[str], cache_ver: int = 0) -> pd.DataFrame:
    ts = _fetch_timestamps(song_id)
    date_start = pd.to_datetime(date_start_iso) if date_start_iso else None
    date_end = pd.to_datetime(date_end_iso) if date_end_iso else None
    ts = _apply_date_range(ts, date_start, date_end)
    if ts.empty:
        return pd.DataFrame(columns=["week_start", "plays", "rolling_4w", "cum_plays"])
    df = pd.DataFrame({"ts": ts})
    # Montag-basierte Wochen
    week = df["ts"].dt.to_period("W-MON").apply(lambda p: p.start_time)
    agg = df.groupby(week).size().rename("plays").to_frame().sort_index()
    agg["rolling_4w"] = agg["plays"].rolling(4, min_periods=1).mean()
    agg["cum_plays"] = agg["plays"].cumsum()
    agg = agg.reset_index().rename(columns={"ts": "week_start"})
    return agg


@cache.memoize(timeout=1800)
def song_interarrival(song_id: str, date_start_iso: Optional[str], date_end_iso: Optional[str], cache_ver: int = 0) -> pd.DataFrame:
    ts = _fetch_timestamps(song_id)
    date_start = pd.to_datetime(date_start_iso) if date_start_iso else None
    date_end = pd.to_datetime(date_end_iso) if date_end_iso else None
    ts = _apply_date_range(ts, date_start, date_end)
    gaps = _gaps_days(ts)
    if gaps.size == 0:
        return pd.DataFrame(columns=["gap_days"])
    return pd.DataFrame({"gap_days": gaps})


@cache.memoize(timeout=1800)
def song_clock(song_id: str, date_start_iso: Optional[str], date_end_iso: Optional[str], cache_ver: int = 0) -> pd.DataFrame:
    ts = _fetch_timestamps(song_id)
    date_start = pd.to_datetime(date_start_iso) if date_start_iso else None
    date_end = pd.to_datetime(date_end_iso) if date_end_iso else None
    ts = _apply_date_range(ts, date_start, date_end)
    if ts.empty:
        return pd.DataFrame({"hour": list(range(24)), "plays": [0]*24})
    hours = ts.dt.hour
    agg = hours.value_counts().sort_index()
    full = pd.Series(0, index=pd.Index(range(24), name="hour"), dtype=int)
    full.update(agg.astype(int))
    return full.reset_index().rename(columns={"index": "hour", 0: "plays"})
