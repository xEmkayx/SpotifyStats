from collections import defaultdict

import dash
from dash import html
import dash_bootstrap_components as dbc

# Reihenfolge der Dropdown-Gruppen (Seiten setzen group=... in register_page)
GROUP_ORDER = ["Charts", "Analyse"]


def make_navbar():
    # Nutzt Dash Pages Registry für Links; Seiten ohne group landen direkt in der Leiste
    pages = sorted((p for p in dash.page_registry.values() if p["path"] != "/"),
                   key=lambda p: (p.get("order") or 50, p["name"]))
    groups = defaultdict(list)
    singles = []
    for page in pages:
        if page.get("group"):
            groups[page["group"]].append(page)
        else:
            singles.append(page)

    items = [dbc.NavItem(dbc.NavLink("Home", href="/"))]
    for group in GROUP_ORDER + sorted(set(groups) - set(GROUP_ORDER)):
        if group not in groups:
            continue
        items.append(dbc.DropdownMenu(
            [dbc.DropdownMenuItem(p["name"], href=p["path"]) for p in groups[group]],
            label=group, nav=True, in_navbar=True,
        ))
    items += [dbc.NavItem(dbc.NavLink(p["name"], href=p["path"])) for p in singles]

    return dbc.Navbar(
        dbc.Container([
        dbc.NavbarBrand("Spotify Stats", href="/", className="me-3"),
        dbc.Nav(items, navbar=True, className="me-auto"),
        dbc.Button([html.I(className="bi bi-arrow-clockwise me-1"), "Refresh Daten"],
        id="btn-refresh", color="secondary", size="sm"),
        ]),
        color="light",
        className="mb-3",
        )
