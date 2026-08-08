from datetime import date, timedelta
from dash import dcc, html
import dash_bootstrap_components as dbc


FILTER_TYPE = "filter"
APPLY_TYPE = "filter-apply"
QUICK_RANGE_TYPE = "quick-range"
METRIC_TOGGLE_TYPE = "metric-toggle"
SIDEBAR_TYPE = "sidebar"
SIDEBAR_TOGGLE_TYPE = "sidebar-toggle"
SIDEBAR_ICON_TYPE = "sidebar-icon"
CATEGORY_TOGGLE_TYPE = "category-toggle"


def catid(scope: str): return {"type": CATEGORY_TOGGLE_TYPE, "scope": scope, "name": "category"}

def fid(scope: str, name: str) -> dict:
    # Eindeutige Dict-ID für einen Filter-Control
    return {"type": FILTER_TYPE, "scope": scope, "name": name}

def aid(scope: str) -> dict:
    # Apply-Button ID
    return {"type": APPLY_TYPE, "scope": scope}


def qid(scope: str, name: str) -> dict:
    return {"type": QUICK_RANGE_TYPE, "scope": scope, "name": name}

def mid(scope: str) -> dict:
    return {"type": METRIC_TOGGLE_TYPE, "scope": scope, "name": "metric"}

def sidebar_id(scope):  # Sidebar-Container
    return {"type": SIDEBAR_TYPE, "scope": scope}

def stid(scope):  # Toggle-Button
    return {"type": SIDEBAR_TOGGLE_TYPE, "scope": scope}

def siid(scope):  # Chevron-Icon
    return {"type": SIDEBAR_ICON_TYPE, "scope": scope}


def form_group(label_text: str, control):
    return html.Div([dbc.Label(label_text, className="form-label d-block"), control], className="mb-3")


def date_range(scope: str, label="Zeitraum", default_days=90):
    today = date.today()
    start = today - timedelta(days=default_days)
    control = dcc.DatePickerRange(
        id=fid(scope, "date"),
        start_date=start,
        end_date=today,
        display_format="YYYY-MM-DD",
        clearable=True,
        className="w-100",  # Breite anpassen
        style={"display": "block"}  # unter dem Label, nicht daneben
    )
    return form_group(label, control)


def topn_slider(scope: str, label="Anzahl Top N", default=30, minv=10, maxv=100, step=10):
    return html.Div([
    dbc.Label(label),
    dcc.Slider(
    id=fid(scope, "top_n"),
    min=minv, max=maxv, step=step, value=default,
    marks={i: str(i) for i in [10, 20, 30, 40, 50, 75, 100] if minv <= i <= maxv}
    )
    ], className="mt-3")


def dropdown(scope: str, name: str, label: str, options, multi=False, placeholder="Bitte wählen"):
    control = dcc.Dropdown(
    id=fid(scope, name),
    options=options,
    multi=multi,
    placeholder=placeholder,
    clearable=True,
    className="w-100"
    )
    return form_group(label, control)


def quick_ranges(scope: str):
    # Drei Shortcut-Buttons: 1 Woche, 1 Monat, 1 Jahr
    return form_group(
        "Schnellauswahl",
        html.Div([
            dbc.Button("Letzte Woche", id=qid(scope, "1w"), size="sm", color="secondary", outline=True,
                       className="me-1"),
            dbc.Button("Letzter Monat", id=qid(scope, "1m"), size="sm", color="secondary", outline=True,
                       className="me-1"),
            dbc.Button("Letztes Jahr", id=qid(scope, "1y"), size="sm", color="secondary", outline=True),
        ], className="d-flex flex-row")
    )


def metric_toggle(scope: str):
    return form_group(
        "Metrik",
        # Wrapper mit eigener Klasse, damit wir gezielt stylen können
        html.Div(
            dbc.RadioItems(
                id=mid(scope),
                className="btn-group segmented-group",  # Gruppe
                inputClassName="btn-check",
                labelClassName="btn",  # bewusst OHNE 'btn-outline-primary'
                labelCheckedClassName="active",
                options=[
                    {"label": "Streams", "value": "plays"},
                    {"label": "Minuten", "value": "minutes"},
                ],
                value="plays",
            ),
            className="segmented-toggle"
        )
    )


def make_sidebar_layout(scope: str, sidebar_children, content_children, title="Filter"):
    # sidebar_children: Liste/Komponente (z. B. dein Filter-Panel)
    # content_children: Hauptinhalt (z. B. Karte mit Graph)
    return html.Div(
    className="sidebar-layout",
    children=[
    html.Div(
    id=sidebar_id(scope),
    className="sidebar",  # wird um 'collapsed' ergänzt
    children=[
    html.Div(
    className="sidebar-header",
    children=[
    html.Div([
    html.I(className="bi bi-funnel me-2"),
    html.Span(title, className="sidebar-title hide-when-collapsed")
    ], className="d-flex align-items-center"),
    dbc.Button(
    html.I(id=siid(scope), className="bi bi-chevron-left"),
    id=stid(scope),
    color="link",
    className="sidebar-toggle-btn",
    )
    ]
    ),
    html.Div(className="sidebar-body hide-when-collapsed-wrap", children=sidebar_children)
    ]
    ),
    html.Div(className="sidebar-content", children=content_children)
    ]
    )


def build_filter_panel(
    scope: str,
    controls: list,
    apply_text: str = "Anwenden",
    with_apply: bool = True,
    variant: str = "plain",      # "plain" für Sidebar, "card" falls du es mal frei stehend nutzen willst
    title: str | None = None     # nur für variant="card" relevant
    ):
    body = controls[:]
    if with_apply:
        body += [
        html.Hr(className="my-3"),
        dbc.Button(
        [html.I(className="bi bi-play-fill me-1"), apply_text],
        id=aid(scope),
        color="primary",
        className="w-100"
        )
        ]

    if variant == "card":
        header = dbc.CardHeader(title) if title else None
        children = [c for c in [header, dbc.CardBody(body)] if c is not None]
        return dbc.Card(children, className="filter-card")

    # Sidebar‑Variante: „plain“ ohne zusätzliche Card/Border
    return html.Div(body, className="filter-panel")


def category_toggle(scope: str):
    return form_group(
    "Kategorie",
    html.Div(
    dbc.RadioItems(
    id=catid(scope),
    className="btn-group segmented-group",
    inputClassName="btn-check",
    labelClassName="btn",
    labelCheckedClassName="active",
    options=[
    {"label": "Songs", "value": "songs"},
    {"label": "Artists", "value": "artists"},
    {"label": "Alben", "value": "albums"},
    ],
    value="songs",
    ),
    className="segmented-toggle"
    )
    )


def category_tabs(scope: str):
    return form_group(
    "Kategorie",
    dbc.Tabs(
    id=catid(scope),            # behält dein Pattern-Matching-ID-Schema
    active_tab="songs",         # default
    children=[
    dbc.Tab(label="Songs",   tab_id="songs"),
    dbc.Tab(label="Artists", tab_id="artists"),
    dbc.Tab(label="Alben",   tab_id="albums"),
    ],
    class_name="w-100"          # füllt die Breite im Sidebar
    )
    )


def text_input(scope: str, name: str, label: str, placeholder=""):
    control = dcc.Input(
    id=fid(scope, name),
    type="text",
    placeholder=placeholder,
    debounce=True,   # vermeidet Callback auf jeden Keypress
    className="w-100"
    )
    return form_group(label, control)
