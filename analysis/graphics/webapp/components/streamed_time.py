from dash import html, dcc, callback, Input, Output
from dash.development.base_component import Component

import dash
import dash_bootstrap_components as dbc
import plotly.express as px
from dash import html, dcc, callback, Input, Output


class StreamedTime:
    def __init__(self, page_name):
        self.page_name = page_name
        self.stream_time_text_id = f'div-stream-time-text-{page_name}'
        self.stream_time_text = init_stream_time_text(self.stream_time_text_id)

        self.stream_time_id = f'div-stream-time-{page_name}'
        self.days_id = f'{self.stream_time_id}-days'
        self.hours_id = f'{self.stream_time_id}-hours'
        self.minutes_id = f'{self.stream_time_id}-minutes'
        self.seconds_id = f'{self.stream_time_id}-seconds'
        self.stream_time = init_stream_time(self.stream_time_id, self.days_id, self.hours_id, self.minutes_id,
                                            self.seconds_id)

        self.total_streams_id = f'div-total-stream-count-{page_name}'
        self.total_streams = init_total_streams(self.total_streams_id)

    def render(self):
        return html.Div(
            children=[
                self.stream_time_text,
                self.total_streams,
                self.stream_time
            ]
        )


def init_stream_time_text(s_id):
    return html.Div(id=s_id)


def init_total_streams(s_id):
    return html.Div(id=s_id)


def init_stream_time(s_id, days_id, hours_id, minutes_id, seconds_id):
    return html.Center(
        html.Div(
            id=s_id,
            className='hz-container',
            children=[
                html.Div(
                    className='date',
                    id=days_id
                ),
                html.Label('D', className='date-text'),
                html.Div(
                    className='date',
                    id=hours_id
                ),
                html.Label('H', className='date-text'),
                html.Div(
                    className='date',
                    id=minutes_id
                ),
                html.Label('M', className='date-text'),
                html.Div(
                    className='date',
                    id=seconds_id
                ),
                html.Label('S', className='date-text', style={'margin-right': '10px'}),
            ]

        )
    )
