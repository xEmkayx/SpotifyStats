import dash_bootstrap_components as dbc
from dash import html

def empty_state(title="Keine Daten", subtitle="Bitte Filter anwenden oder Zeitraum anpassen.", icon="bi bi-bar-chart"):
    return html.Div(
    className="empty-state",
    children=dbc.Stack(
    [
    html.I(className=f"{icon} empty-icon"),
    html.Div(title, className="empty-title"),
    html.Div(subtitle, className="empty-subtitle"),
    ],
    gap=2,
    className="align-items-center justify-content-center text-center"
    )
    )

def skeleton_graph(height=520):
    # Placeholder als „Skelett“, wenn du lieber eine Ladefläche zeigen willst
    return dbc.Placeholder(animation="glow", style={"height": f"{height}px", "width": "100%", "borderRadius": "8px"})
