import dash_bootstrap_components as dbc
from dash import html, dcc


class StreamSortSwitchButton:
    def __init__(self, page_name):
        self.page_name = page_name
        self.id = f"{self.page_name}-streamed-by-radios"

    def get_id(self):
        return self.id

    def render(self):
        return html.Div(
            [
                dbc.RadioItems(
                    id=self.id,
                    className="btn-group",
                    inputClassName="btn-check",
                    labelClassName="btn btn-outline-primary",
                    labelCheckedClassName="active",
                    options=[
                        {"label": "Sort by total count of Streams", "value": 1},
                        {"label": "Sort by total streamed minutes", "value": 2},
                    ],
                    value=1,
                )
            ],
            className="radio-group",
        )
