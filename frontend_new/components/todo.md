Hier ist ein kurzer, praxistauglicher Workflow, wie du in deiner aktuellen Struktur eine neue Seite sauber hinzufügst – wiederholbar für jede weitere Seite.

    Fachlich festlegen

    Scope/Slug wählen: z. B. SCOPE = "top-artists", Pfad "/top-artists", Seitentitel "Top Artists".
    Welche Visualisierung? (Balken vs. Säulen, Tabelle). Welche Metriken? (plays, minutes). Welche Filter? (Datum, Top N, ggf. Artist/Album/Genre).

2. Daten/Service anlegen

    Datei: services/<neue_seite>.py
    Prinzip: Pushdown in SQL, Overcount vermeiden, Caching nutzen.
        Plays zählen als COUNT(DISTINCT sh.played_at) in einer Voraggregation.
        seconds_total = plays * song_length_seconds (über length_seconds_expr).
        Artists/Alben nur über separate voraggregierte Joins ergänzen (keine Duplikation).
    API:
        fetch<seite>(start_dt: str, end_dt: str, limit: int, metric: str) -> pd.DataFrame
        cached_<seite>(..., cache_version: int) -> pd.DataFrame via @cache.memoize
    Optional: Helper, die nur IDs/Order zurückgeben (für Playlist- oder Download-Funktionen).

3. Reusable Komponenten prüfen/erweitern

    Filters: Falls neue Controls nötig sind (z. B. Dropdown „Genre“), Baustein in components/filters.py ergänzen (form_group + Dict-ID via fid(scope, "genre")).
    Charts: Neue Builder-Funktion in components/charts.py erstellen, die auf style_fig/das Template zurückgreift (z. B. build_top_artists_figure(df, metric, top_n, dark=False)).
    Empty-State/Skeleton sind schon vorhanden; wiederverwenden.

4. Page-Datei anlegen

    Datei: pages/<slug>.py
    Pattern:
        dash.register_page(name, path="/<slug>", name="Titel")
        layout(): links Sidebar via make_sidebar_layout(...), rechts Card mit Header (+ metric_toggle, optional Playlist- oder Download-Button), Body enthält html.Div(id="<scope>-visual", children=skeleton_graph()).
        Filterpanel via build_filter_panel(scope=SCOPE, controls=[date_range, quick_ranges, topn_slider,…], variant="plain", with_apply=True).
        Callbacks:
            Quick-Range: setzt DatePickerRange (ctx.triggered_id).
            Update Visual: Output("<scope>-visual", "children"); Inputs: Apply-Button, Metric-Toggle; States: Datum, TopN, cache-version. Holt df aus cached_<seite>, gibt dcc.Graph zurück oder empty_state bei leer.
            Summaries: falls gewünscht über services/summary.
            Sidebar-Toggle: wie auf Top-Songs (sidebar_id/stid/siid).
    IDs immer mit scope-Namespacing (fid/aid/mid/qid) – dann gibt es keine Kollisionen.

5. Navbar/Navigation

    Wenn deine Navbar dynamisch aus dash.page_registry baut, erscheint die neue Seite automatisch.
    Wenn statisch: Link in components/navbar.py ergänzen.

6. Styling

    Nichts weiter nötig: Cards/Buttons/Segmente folgen deinem Theme und custom.css. Falls ein spezieller Toggle nötig ist, unter eigener Klasse kapseln (wie segmented-toggle).

7. Performance-/Qualitätscheck

    SQL explain prüfen, ob Index stream_history(played_at) und ggf. (song_id, played_at) greifen.
    Caching: timeout in config.py; Cache-Key enthält (start_dt, end_dt, limit, metric, cache_version).
    Payload: nur aggregierte Daten (Top N) ans Frontend senden.
    UI: uirevision in Plotly setzen, damit Zoom/Scroll bei Updates bestehen bleibt.

8. Fehler-/Empty-Handling

    Bei Exceptions im Service: im Callback empty_state("Fehler beim Laden", str(e), icon="bi bi-exclamation-triangle") anzeigen.
    Bei leeren Daten: empty_state mit Hinweis zur Filteranpassung.

Mini-Templates zum Kopieren

services/top_artists.py (Skeleton)
from sqlalchemy import text
import pandas as pd
from core.db import engine
from core.extensions import cache
from services.sql_fragments import played_at_cast_expr, length_seconds_expr

CAST = played_at_cast_expr()
LEN  = length_seconds_expr("s")

PLAYS_PER_SONG = f"""
SELECT sh.song_id, COUNT(DISTINCT sh.played_at) AS plays
FROM stream_history sh
WHERE {CAST} BETWEEN :start_dt AND :end_dt
GROUP BY sh.song_id
"""

SQL = f"""
SELECT
ar.artist_id,
ar.artist_name,
SUM(p.plays) AS plays,
SUM(p.plays * {LEN}) AS seconds_total
FROM ({PLAYS_PER_SONG}) p
JOIN songs s ON s.song_id = p.song_id
JOIN art_songs asg ON asg.song_id = s.song_id
JOIN artists ar ON ar.artist_id = asg.artist_id
GROUP BY ar.artist_id, ar.artist_name
"""

def _fetch_top_artists(start_dt: str, end_dt: str, limit: int, metric: str) -> pd.DataFrame:
order_col = "plays" if (metric or "plays") == "plays" else "seconds_total"
sql = SQL + f" ORDER BY {order_col} DESC LIMIT :limit"
with engine.begin() as conn:
rows = conn.execute(text(sql), {"start_dt": start_dt, "end_dt": end_dt, "limit": limit}).mappings().all()
return pd.DataFrame([dict(r) for r in rows])

@cache.memoize(timeout=900)
def cached_top_artists(start_dt, end_dt, limit, metric, cache_version):
return _fetch_top_artists(start_dt, end_dt, limit, metric)

pages/top_artists.py (Skeleton)
import dash
from dash import dcc, html, Input, Output, State, callback, no_update, ctx
import dash_bootstrap_components as dbc
from components.filters import build_filter_panel, date_range, quick_ranges, topn_slider, metric_toggle, fid, aid, qid, mid, sidebar_id, stid, siid
from components.empty_state import empty_state, skeleton_graph
from components.summaries import listening_time_summary, sid as summary_id
from components.sidebar import make_sidebar_layout
from components.charts import build_top_artists_figure  # erstelle analog zu top_songs
from services.top_artists import cached_top_artists
from services.summary import cached_total_listening_seconds, format_duration_de

SCOPE = "top-artists"
dash.register_page(name, path="/top-artists", name="Top Artists")

def layout():
filters = build_filter_panel(SCOPE, [date_range(SCOPE), quick_ranges(SCOPE), topn_slider(SCOPE, default=20)], with_apply=True, variant="plain")
right = [
listening_time_summary(SCOPE),
dbc.Card([
dbc.CardHeader(dbc.Row([
dbc.Col("Top Artists"),
dbc.Col(metric_toggle(SCOPE), width="auto", className="ms-auto")
], className="g-2")),
dbc.CardBody(dcc.Loading(children=html.Div(id=f"{SCOPE}-visual", children=skeleton_graph())))
])
]
return make_sidebar_layout(SCOPE, filters, right, title="Filter")

@callback(
Output(fid(SCOPE, "date"), "start_date"),
Output(fid(SCOPE, "date"), "end_date"),
Input(qid(SCOPE, "1w"), "n_clicks"),
Input(qid(SCOPE, "1m"), "n_clicks"),
Input(qid(SCOPE, "1y"), "n_clicks"),
)
def set_quick_range(n1, n2, n3):
from datetime import date, timedelta
if not ctx.triggered_id: return no_update, no_update
today = date.today()
m = ctx.triggered_id["name"]
start = today - timedelta(days=7 if m=="1w" else 30 if m=="1m" else 365)
return start, today

@callback(
Output(f"{SCOPE}-visual", "children"),
Input(aid(SCOPE), "n_clicks"),
Input(mid(SCOPE), "value"),
State(fid(SCOPE, "date"), "start_date"),
State(fid(SCOPE, "date"), "end_date"),
State(fid(SCOPE, "top_n"), "value"),
State("cache-version", "data"),
)
def update_visual(n_apply, metric, start_date, end_date, top_n, cache_ver):
if not start_date or not end_date:
return empty_state("Keine Daten", "Bitte Zeitraum wählen.")
df = cached_top_artists(f"{start_date} 00:00", f"{end_date} 23:59", int(top_n or 20), (metric or "plays"), int(cache_ver or 0))
if df.empty:
return empty_state("Keine Treffer", "Filter anpassen.", icon="bi bi-funnel")
fig = build_top_artists_figure(df, metric or "plays", int(top_n or 20))
return dcc.Graph(figure=fig, config={"displayModeBar": True})

@callback(
Output(summary_id(SCOPE, "listening_time"), "children"),
Input(aid(SCOPE), "n_clicks"),
State(fid(SCOPE, "date"), "start_date"),
State(fid(SCOPE, "date"), "end_date"),
State("cache-version", "data"),
)
def update_summary(_, start_date, end_date, cache_ver):
if not start_date or not end_date: return no_update
secs = cached_total_listening_seconds(f"{start_date} 00:00", f"{end_date} 23:59", int(cache_ver or 0))
return f"(Ungefähre) Gesamte Hörzeit: {format_duration_de(secs)}"

@callback(
Output(sidebar_id(SCOPE), "className"),
Output(siid(SCOPE), "className"),
Input(stid(SCOPE), "n_clicks"),
State(sidebar_id(SCOPE), "className"),
)
def toggle_sidebar(n, cls):
if not n: return cls or "sidebar", "bi bi-chevron-left"
cls = cls or "sidebar"
collapsed = "collapsed" in cls
return ("sidebar" if collapsed else "sidebar collapsed",
"bi bi-chevron-left" if collapsed else "bi bi-chevron-right")

Damit hast du:

    Klare 3‑Schichten (Services, Components, Pages)
    Einheitliche IDs/Scopes
    Sofort lauffähige Navigation
    Wiederverwendbare Filter/Empty/Summary/Sidebar
    Saubere Performance (Pushdown + Cache)

Wenn du mir sagst, welche Seite du als Nächstes planst (z. B. Timeline „Plays über Zeit“, Top Alben, Interaktive Tabelle), skizziere ich dir die jeweils passende Service‑SQL und die Chart‑Funktion.