import dash
from dash import html
import dash_bootstrap_components as dbc

def make_navbar():
    # Nutzt Dash Pages Registry für Links
    links = []
    # Sortierung optional
    for page in dash.page_registry.values():
        # page["path"], page["name"]
        # Home zuerst
        if page["path"] == "/":
            continue
        links.append(dbc.NavItem(dbc.NavLink(page["name"], href=page["path"])))

    return dbc.Navbar(
        dbc.Container([
        dbc.NavbarBrand("Spotify Stats", className="me-3"),
        dbc.Nav([dbc.NavItem(dbc.NavLink("Home", href="/"))] + links,
        navbar=True, className="me-auto"),
        dbc.Button([html.I(className="bi bi-arrow-clockwise me-1"), "Refresh Daten"],
        id="btn-refresh", color="secondary", size="sm"),
        ]),
        color="light",
        className="mb-3",
        )
