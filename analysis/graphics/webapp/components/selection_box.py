import dash_bootstrap_components as dbc
from dash import html, dcc

from analysis.graphics.webapp.helpers.consts import *

DATEPICKER_NAME = 'date-picker'
INPUT_NAME = 'inp-amount'
B7D_NAME = 'button-7d'
BMONTH_NAME = 'button-month'
BYEAR_NAME = 'button-year'
BTN_GROP_NAME = 'btn-group'


class SelectionBox:
    def __init__(self, page_name, children: list | None = None, **kwargs):
        self.children = children or []
        self.page_name = page_name
        self.datepicker_id = f'{DATEPICKER_NAME}-{page_name}'
        self.input_id = f'{INPUT_NAME}-{page_name}'
        self.button_ids = {
            B7D_NAME: f'{B7D_NAME}-{page_name}',
            BMONTH_NAME: f'{BMONTH_NAME}-{page_name}',
            BYEAR_NAME: f'{BYEAR_NAME}-{page_name}'
        }
        self.bgroup_id = f'{BTN_GROP_NAME}-{page_name}'

        self.datepicker = init_datepicker(self.datepicker_id)
        self.input = init_input_textbox(self.input_id)
        # html.Br(),
        self.buttons = init_buttons(self.button_ids, self.bgroup_id)

    def get_datepicker_id(self):
        return self.datepicker_id

    def get_input_id(self):
        return self.input_id

    def get_buttons_ids(self):
        return self.button_ids

    def render(self, children: list | None = None):
        if children is not None:
            self.children.append(*children)
        container = html.Div(
            children=[
                self.datepicker,
                self.input,
                html.Br(),
                self.buttons,
                *self.children
            ]
        )
        return container


class ExtendedSelectionBox(SelectionBox):
    def __init__(self, page_name, children: list | None = None, **kwargs):
        super().__init__(page_name, children, **kwargs)

        self.streamed_by_buttons_id = ''
        self.playlist_button_id = ''

        self.streamed_by_buttons = ''
        self.playlist_button = ''

    def get_streamed_by_buttons_id(self):
        return self.streamed_by_buttons_id

    def get_playlist_button_id(self):
        return self.playlist_button_id

    def render(self, children: list | None = None):
        if children is not None:
            self.children.append(*children)
        container = html.Div(
            children=[
                self.datepicker,
                self.input,
                html.Br(),
                self.buttons,
                self.streamed_by_buttons,
                self.playlist_button,
                *self.children
            ]
        )
        return container


##############
### Methods
##############
def init_datepicker(obj_id):
    datepicker = dcc.DatePickerRange(
        id=obj_id,
        min_date_allowed=date(2010, 1, 1),
        max_date_allowed=TOMORROW_DATE,  # date(2022, 12, 12),  #
        initial_visible_month=date.today(),  # date(2022, 11, 1),  #
        end_date=TOMORROW_DATE,
        start_date=date(datetime.now().year, 1, 1)
    )
    return datepicker


def init_input_textbox(obj_id):
    amount_tb = dbc.Input(
        id=obj_id,
        type='number',
        value=10,
        className='inp-summary',
        style={
            'width': '4%',
            'margin-left': '5px',
            'margin-right': '5px',
            'display': 'inline-block',
            # 'filter': 'contrast(200%)',
        }
    )
    return amount_tb


def init_buttons(button_ids, bgroup_id):
    button_7d = dbc.Button(
        'Letzte 7 Tage',
        id=button_ids[B7D_NAME],
        outline=True,
        color='primary',
        n_clicks=0
    )

    button_month = dbc.Button(
        'Letzter Monat',
        id=button_ids[BMONTH_NAME],
        outline=True,
        color='primary',
        n_clicks=0
    )

    button_year = dbc.Button(
        'Letztes Jahr',
        id=button_ids[BYEAR_NAME],
        outline=True,
        color='primary',
        n_clicks=0
    )

    buttons = dbc.ButtonGroup(
        id=bgroup_id,
        children=[
            button_7d,
            button_month,
            button_year
        ]
    )
    return buttons


def init_streamed_by_buttons():
    pass


def init_hoerzeit():
    pass


def init_create_playlist_button():
    pass
