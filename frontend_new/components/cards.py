from dash import html
import dash_bootstrap_components as dbc


def cards_grid(items: list[dict], kind: str, cols: dict | None = None, gutter="g-2", min_card_px: int = 230):
    # Map für Bootstrap-g-* zu echten Abständen
    gap_map = {"g-0": "0", "g-1": ".25rem", "g-2": ".5rem", "g-3": "1rem", "g-4": "1.5rem", "g-5": "3rem"}
    gap_val = gap_map.get(gutter, ".5rem")

    def make_card(it):
        img = html.Img(
            src=it.get("image_url"),
            **{"data-src": it.get("image_url") or ""},
            alt="",
            className="card-img-top lazy-img",
            style={"aspectRatio": "1 / 1", "objectFit": "cover"},
        )
        body = dbc.CardBody([
            html.Div(it.get("title", ""), className="fw-semibold text-truncate"),
            html.Small(it.get("subtitle", ""), className="text-muted d-block mt-1"),
        ])
        footer = dbc.CardFooter(it.get("footer", ""), className="text-muted") if it.get("footer") else None
        card_inner = [img, body, footer] if footer else [img, body]
        return html.A(
            dbc.Card(card_inner, className="h-100 card-compact"),
            href=it.get("href") or "#",
            target="_blank",
            style={"display": "block"}  # füllt die Grid-Zelle
        )

    # Fallback: feste Bootstrap-Breakpoints, wenn cols übergeben wurden
    if cols:
        cls = [gutter]
        for bp, n in cols.items():
            cls.append(f"row-cols-{bp}-{n}" if bp != "xs" else f"row-cols-{n}")
        return dbc.Row([dbc.Col(make_card(it)) for it in items], className=" ".join(cls))

    # Standard: fluides CSS Grid (wichtig: display + gridTemplateColumns + gap)
    return html.Div(
        [html.Div(make_card(it), style={"width": f"min(100%, {min_card_px}px)"}) for it in items],
        className="cards-grid",
        style={
            "display": "flex",
            "flexWrap": "wrap",
            "gap": gap_val,
            "justifyContent": "center",
            "alignItems": "stretch",
        }
    )


def map_song_items(df):
    out = []
    for _, r in df.iterrows():
        out.append({
        "title": r["song_name"],
        "subtitle": r.get("artists", ""),
        "image_url": r.get("image_url") or "",
        "footer": f'{int(r["plays"])} Streams • {round(r["seconds_total"]/60, 1)} Min',
        "href": f'https://open.spotify.com/track/{r["song_id"]}'
        })
    return out

def map_artist_items(df):
    out = []
    for _, r in df.iterrows():
        out.append({
        "title": r["artist_name"],
        "subtitle": "",
        "image_url": r.get("image_url") or "",
        "footer": f'{int(r["plays"])} Streams • {round(r["seconds_total"]/60, 1)} Min',
        "href": f'https://open.spotify.com/artist/{r["artist_id"]}'
        })
    return out

def map_album_items(df):
    out = []
    for _, r in df.iterrows():
        out.append({
        "title": r["album_name"],
        "subtitle": r.get("artists", ""),
        "image_url": r.get("image_url") or "",
        "footer": f'{int(r["plays"])} Streams • {round(r["seconds_total"]/60, 1)} Min',
        "href": f'https://open.spotify.com/album/{r["album_id"]}'
        })
    return out
