from dash import html
import dash_bootstrap_components as dbc


class SingleTypeSelection:
    def __init__(self, selection_type):
        self.selection_type = selection_type
        self.rb_selection_method_id = f'radio-items-{self.selection_type}'
        self.input_name_id = f'inp-name-{self.selection_type}'
        self.input_limit_id = f'inp-limit-{self.selection_type}'

        self.rb_selection_method = init_rb_selection_methods(self.rb_selection_method_id,
                                                             str(self.selection_type).title())
        self.input_name = init_input_name(self.input_name_id, str(self.selection_type).title())
        self.input_limit = init_input_limit(self.input_limit_id)

    def render(self):
        return html.Div(
            children=[
                self.input_name,
                self.input_limit,
                html.Br(),
                self.rb_selection_method,
            ]
        )


def init_rb_selection_methods(item_id, selection_type):
    return html.Div(
        [
            dbc.RadioItems(
                id=item_id,
                className="btn-group",
                inputClassName="btn-check",
                labelClassName="btn btn-outline-primary",
                labelCheckedClassName="active",
                options=[
                    {"label": f"{selection_type} Name", "value": 1},
                    {"label": f"{selection_type} ID", "value": 2},
                ],
                value=1,
            )
        ],
        className="radio-group",
    )


def init_input_name(item_id, selection_type):
    return dbc.Input(type='text',
                     id=item_id,
                     placeholder=f"Insert {selection_type} here...",
                     style={
                         'width': '10%',
                         'margin-left': '5px',
                         'margin-right': '5px',
                         'display': 'inline-block',
                     }
                     )


def init_input_limit(item_id):
    return dbc.Input(type='number',
                     id=item_id,
                     value=20,
                     # className='inp-summary',
                     style={
                         'width': '4%',
                         'margin-left': '5px',
                         'margin-right': '5px',
                         'display': 'inline-block',
                     }
                     )
