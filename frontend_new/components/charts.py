from datetime import date, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go

pio.templates.default = "simple_white"


def _build_top_entity_figure(
        df: pd.DataFrame,
        metric: str,
        top_n: int,
        dark: bool,
        *,
        y_col: str,
        y_title: str,
        title_label: str,
        uirevision: str,
        with_artists: bool
):
    if df.empty:
        fig = px.bar(title="Keine Daten im gewählten Zeitraum.")
        fig.update_layout(height=500)
        return fig

    # Metrik bestimmen
    if metric == "minutes":
        df = df.copy()
        df["minutes"] = (df["seconds_total"] / 60).round(2)
        x_col = "minutes"
        x_title = "Gestreamte Minuten"
        title = f"Top {min(len(df), int(top_n))} {title_label} (nach Minuten)"
    else:
        x_col = "plays"
        x_title = "Anzahl Streams"
        title = f"Top {min(len(df), int(top_n))} {title_label} (nach Streams)"

    # Sortierung und Chart
    df = df.sort_values(x_col, ascending=True)
    hover_data = ({x_col: True, y_col: False}
                  if not with_artists
                  else {"artists": True, x_col: True, y_col: False})

    fig = px.bar(
        df, x=x_col, y=y_col,
        hover_data=hover_data,
        orientation="h",
        title=title
    )
    fig.update_layout(
        xaxis_title=x_title,
        yaxis_title=y_title,
        height=600,
        margin=dict(l=10, r=10, t=60, b=10),
        uirevision=uirevision
    )
    if with_artists:
        fig.update_traces(hovertemplate="<b>%{y}</b><br>Artists: %{customdata[0]}<br>Wert: %{x}<extra></extra>")
    else:
        fig.update_traces(hovertemplate="<b>%{y}</b><br>Wert: %{x}<extra></extra>")

    # Optional: Theme anwenden
    # return style_fig(fig, dark)
    return fig


def build_top_songs_figure(df: pd.DataFrame, metric: str, top_n: int, dark: bool):
    return _build_top_entity_figure(
        df, metric, top_n, dark,
        y_col="song_name",
        y_title="Song Name",
        title_label="Songs",
        uirevision="ts",
        with_artists=True
    )


def build_top_artists_figure(df: pd.DataFrame, metric: str, top_n: int, dark: bool):
    return _build_top_entity_figure(
        df, metric, top_n, dark,
        y_col="artist_name",
        y_title="Artist",
        title_label="Artists",
        uirevision="ta",
        with_artists=False
    )


def build_top_albums_figure(df: pd.DataFrame, metric: str, top_n: int, dark: bool):
    return _build_top_entity_figure(
        df, metric, top_n, dark,
        y_col="album_name",
        y_title="Album",
        title_label="Alben",
        uirevision="tal",
        with_artists=True
    )


def build_song_heatmap_figure(daily_df: pd.DataFrame, year: int, dark: bool):
    # Vollständigen Jahreskalender aufbauen
    y = int(year)
    start = date(y, 1, 1)
    end   = date(y, 12, 31)

    all_days = pd.date_range(start, end, freq="D").date
    base = pd.DataFrame({"day": all_days})
    if daily_df is None or daily_df.empty:
        df = base.assign(plays=0)
    else:
        df = base.merge(daily_df[["day", "plays"]], on="day", how="left").fillna({"plays": 0})
        df["plays"] = df["plays"].astype(int)

    # Wochentag (0=Mo .. 6=So) und Wochenindex relativ zum ersten Montag
    dow = pd.Series([d.weekday() for d in df["day"]])
    first_monday = start - timedelta(days=start.weekday())
    week_index = pd.Series([(d - first_monday).days // 7 for d in df["day"]])

    df["dow"] = dow
    df["w"] = week_index

    # Pivot in 7 x N
    pivot = df.pivot_table(index="dow", columns="w", values="plays", aggfunc="sum", fill_value=0)
    # Sicherstellen, dass alle Wochentage vorhanden sind
    pivot = pivot.reindex(index=[0,1,2,3,4,5,6], fill_value=0)

    # Hovertexte: Matrix gleicher Form
    weekday_labels = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    # Mapping (dow, w) -> Datum
    date_map = {}
    for d, w in zip(df["day"], df["w"]):
        date_map[(d.weekday(), w)] = d

    hovertext = []
    for r in range(7):
        row = []
        for c in pivot.columns:
            d = date_map.get((r, c))
            if d is None or not (start <= d <= end):
                row.append("")
            else:
                row.append(f"{d.isoformat()}<br>Plays: {int(pivot.loc[r, c])}")
        hovertext.append(row)

    # Farbskala an Outlier anpassen
    vmax = int(np.percentile(pivot.values.flatten(), 95)) if pivot.values.size else 1
    vmax = max(vmax, int(pivot.values.max()) if pivot.values.size else 1, 1)

    colorscale_light = [
        [0.0,  "#ebedf0"],
        [0.1,  "#c6e48b"],
        [0.3,  "#7bc96f"],
        [0.6,  "#239a3b"],
        [1.0,  "#196127"],
    ]
    colorscale_dark = [
        [0.0,  "#161b22"],
        [0.1,  "#0e4429"],
        [0.3,  "#006d32"],
        [0.6,  "#26a641"],
        [1.0,  "#39d353"],
    ]
    cs = colorscale_dark if dark else colorscale_light

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,   # Wochenindex
        y=[weekday_labels[i] for i in pivot.index],
        text=hovertext,
        hoverinfo="text",
        colorscale=cs,
        zmin=0,
        zmax=vmax,
        showscale=True,
        colorbar=dict(title="Plays", thickness=10, len=0.7)
    ))

    # Monatstitel an ersten Montagen der Monate
    month_firsts = [date(y, m, 1) for m in range(1, 13)]
    month_ticks = []
    month_labels = []
    for d0 in month_firsts:
        w = (d0 - first_monday).days // 7
        month_ticks.append(w)
        month_labels.append(d0.strftime("%b"))

    fig.update_layout(
        title=f"Hör-Historie {y} (Song)",
        xaxis=dict(
            showgrid=False, zeroline=False, showline=False,
            tickmode="array", tickvals=month_ticks, ticktext=month_labels
        ),
        yaxis=dict(
            showgrid=False, zeroline=False, showline=False,
            tickmode="array", tickvals=[weekday_labels[i] for i in pivot.index]
        ),
        margin=dict(l=10, r=10, t=60, b=10),
        height=220,  # kompakt wie GitHub
        uirevision=f"song-heatmap-{y}",
    )

    # Optional dein globales Styling
    # fig = style_fig(fig, dark)
    return fig


def build_song_lifecycle_figure(weekly_df: pd.DataFrame, dark: bool):
    import plotly.graph_objects as go
    fig = go.Figure()
    if weekly_df is None or weekly_df.empty:
        fig.update_layout(title="Lifecycle (keine Daten)", height=350)
        return fig

    x = pd.to_datetime(weekly_df["week_start"])
    fig.add_trace(go.Bar(
        x=x, y=weekly_df["plays"], name="Plays/Woche",
        marker_color="#4e79a7"
    ))
    fig.add_trace(go.Scatter(
        x=x, y=weekly_df["rolling_4w"], name="Ø 4W rolling",
        mode="lines", line=dict(color="#f28e2b", width=2)
    ))
    fig.add_trace(go.Scatter(
        x=x, y=weekly_df["cum_plays"], name="Kumulativ",
        mode="lines", line=dict(color="#59a14f", width=2, dash="dot"),
        yaxis="y2"
    ))
    fig.update_layout(
        title="Song Lifecycle (Woche)",
        xaxis_title="Woche (Start Mo)",
        yaxis_title="Plays",
        yaxis2=dict(
            title="Kumulativ",
            overlaying="y",
            side="right",
            showgrid=False
        ),
        height=350,
        margin=dict(l=10, r=10, t=50, b=10),
        barmode="overlay",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
    )
    return fig


def build_listening_clock_figure(clock_df: pd.DataFrame, dark: bool):
    import plotly.graph_objects as go
    if clock_df is None or clock_df.empty:
        clock_df = pd.DataFrame({"hour": list(range(24)), "plays": [0]*24})
    # Stunden als 0..23 → Winkel
    theta = clock_df["hour"].astype(int) * (360 / 24.0)
    r = clock_df["plays"].astype(float)

    fig = go.Figure(go.Barpolar(
        r=r,
        theta=theta,
        width=[(360/24.0)*0.9]*len(theta),
        marker_color=r,
        marker_colorscale="Viridis",
        marker_line_color="white",
        marker_line_width=1,
        hovertemplate="Stunde %{customdata}:00<br>Plays: %{r}<extra></extra>",
        customdata=clock_df["hour"]
    ))
    fig.update_layout(
        title="Listening Clock (24h)",
        polar=dict(
            radialaxis=dict(showline=False, ticks="", gridcolor="rgba(200,200,200,0.2)"),
            angularaxis=dict(direction="clockwise", rotation=90, tickmode="array",
                             tickvals=[i*(360/24.0) for i in range(24)],
                             ticktext=[str(i) for i in range(24)])
        ),
        margin=dict(l=10, r=10, t=50, b=10),
        height=350,
        showlegend=False
    )
    return fig


def build_interarrival_hist_figure(gaps_df: pd.DataFrame, dark: bool):
    import plotly.express as px
    import plotly.graph_objects as go
    if gaps_df is None or gaps_df.empty:
        # Keine Daten: leere Figure mit Titel
        fig = go.Figure()
        fig.update_layout(
            title="Inter-Arrival (keine Daten)",
            xaxis_title="Tage zwischen Plays",
            yaxis_title="Anzahl",
            height=350,
            margin=dict(l=10, r=10, t=50, b=10)
        )
        return fig

    # sinnvolle Obergrenze für X-Achse (z. B. 95%-Perzentil), um Ausreißer zu deckeln
    x = gaps_df["gap_days"].astype(float)
    upper = float(np.percentile(x, 95)) if len(x) > 0 else None
    if upper is not None and upper > 0:
        x = x.clip(upper=upper)

    fig = px.histogram(x=x, nbins=30, title="Inter-Arrival Times (Tage)")
    fig.update_layout(
        xaxis_title="Tage zwischen Plays",
        yaxis_title="Anzahl",
        height=350,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    return fig
