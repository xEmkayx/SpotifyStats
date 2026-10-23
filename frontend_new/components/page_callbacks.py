"""
    Wiederkehrende Callbacks (Sidebar-Toggle, Schnellauswahl) für Seiten mit Filter-Sidebar.
"""
from datetime import date, timedelta

import dash
from dash import Input, Output, State, callback, ctx, ALL

from frontend_new.components.filters import fid, qid, sidebar_id, siid, stid

QUICK_RANGE_DAYS = {"1w": 7, "1m": 30, "1y": 365}


def register_sidebar_toggle(scope: str):
    @callback(
        Output(sidebar_id(scope), "className"),
        Output(siid(scope), "className"),
        Input(stid(scope), "n_clicks"),
        State(sidebar_id(scope), "className"),
    )
    def toggle_sidebar(n, cls):
        if not n:
            return cls or "sidebar", "bi bi-chevron-left"
        cls = cls or "sidebar"
        collapsed = "collapsed" in cls
        return ("sidebar" if collapsed else "sidebar collapsed",
                "bi bi-chevron-left" if collapsed else "bi bi-chevron-right")


def register_quick_ranges(scope: str):
    @callback(
        Output(fid(scope, "date"), "start_date"),
        Output(fid(scope, "date"), "end_date"),
        Input(qid(scope, ALL), "n_clicks"),
        prevent_initial_call=True
    )
    def set_quick_range(_):
        trg = ctx.triggered_id
        if not isinstance(trg, dict):
            raise dash.exceptions.PreventUpdate
        today = date.today()
        return today - timedelta(days=QUICK_RANGE_DAYS.get(trg.get("name"), 365)), today
