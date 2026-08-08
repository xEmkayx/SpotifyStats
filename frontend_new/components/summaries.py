from dash import html
import dash_bootstrap_components as dbc

SUMMARY_TYPE = "summary"

def sid(scope: str, name: str) -> dict:
    return {"type": SUMMARY_TYPE, "scope": scope, "name": name}

def listening_time_summary(scope: str):
    return dbc.Card([
    dbc.CardHeader("Gesamte Hörzeit"),
    dbc.CardBody([
    html.Div(id=sid(scope, "listening_time"), className="fw-semibold"),
    ], className="py-2")
    ], className="mb-3")
