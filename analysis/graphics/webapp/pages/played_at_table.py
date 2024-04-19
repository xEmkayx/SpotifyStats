from typing import Dict, Any

import dash
import dash_bootstrap_components as dbc
from aio import ThemeChangerAIO
from dash import html, dcc, callback, Input, Output, State

from analysis.graphics.webapp.components.create_playlist_button import CreatePlaylistButton
from analysis.graphics.webapp.components.selection_box import SelectionBox, B7D_NAME, BMONTH_NAME, BYEAR_NAME
from analysis.graphics.webapp.components.streamed_time import StreamedTime
from analysis.graphics.webapp.helpers import name_helpers
from analysis.graphics.webapp.helpers.time_functions import *

from analysis.graphics.webapp.select_statements import *
from analysis.graphics.webapp.df_files import ndf_helper
from analysis.graphics.webapp.helpers.consts import *

dash.register_page(__name__)

current_filename = name_helpers.get_current_file_name(__file__)
sb = SelectionBox(current_filename)
datepicker_id = sb.get_datepicker_id()
b_ids: dict[Any, Any] = sb.get_buttons_ids()
b7d_id = b_ids[B7D_NAME]
bmonth_id = b_ids[BMONTH_NAME]
byear_id = b_ids[BYEAR_NAME]
input_id = sb.get_input_id()

playlist_button = CreatePlaylistButton(current_filename)
playlist_button_id = playlist_button.get_id()

streamed_time = StreamedTime(current_filename)

# table = dbc.Table.from_dataframe(gr.head(n=1000), striped=True, bordered=True, hover=True)
table = dbc.Table(id='played-at-table-table')
layout = html.Div(
    [
        html.H1(
            ['Stream History']
        ),
        sb.render(),
        html.Br(),
        streamed_time.render(),
        table,
    ]
)


@callback(
    Output(datepicker_id, 'start_date'),
    Output(datepicker_id, 'end_date'),
    Output(b7d_id, 'n_clicks'),
    Output(bmonth_id, 'n_clicks'),
    Output(byear_id, 'n_clicks'),

    [Input(b7d_id, "n_clicks"),
     Input(bmonth_id, 'n_clicks'),
     Input(byear_id, 'n_clicks')
     ]
)
def button_events_graph(b7d, bmonth, byear):
    if b7d != 0:
        res = get_7days()
    elif bmonth != 0:
        res = get_last_month()
    elif byear != 0:
        res = get_last_year()
    else:
        res = get_standard_time()

    s_date = res[0]
    e_date = res[1]

    return s_date, e_date, 0, 0, 0


@callback(
    Output('played-at-table-table', 'children'),
    Output(streamed_time.stream_time_text_id, 'children'),
    Output(streamed_time.total_streams_id, 'children'),
    Output(streamed_time.days_id, 'children'),
    Output(streamed_time.hours_id, 'children'),
    Output(streamed_time.minutes_id, 'children'),
    Output(streamed_time.seconds_id, 'children'),

    Input(DATAFRAME_STORE_ID, 'data'),
    Input(datepicker_id, 'start_date'),
    Input(datepicker_id, 'end_date'),
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value")
)
def update_graph_theme(df_store, start_date, end_date, theme):
    # ndf = pd.DataFrame.from_dict(df_store)
    ndf = pd.DataFrame(df_store)
    # print('table')
    # print(ndf)
    df = ndf_helper.get_played_at_table(df=ndf, start_date=start_date, end_date=end_date)
    # df = dataframe_helpers.get_played_at_table(start_date=start_date, end_date=end_date)
    """
    df['Played at'] = pd.to_datetime(df['Played at'], format='%Y-%m-%d %H:%M')
    print('played at df:')
    print(df.head(n=5).to_string())

    mask = (df['Played at'] >= start_date) & (df['Played at'] <= end_date)
    # print(f'mask: {mask}')

    ndf = df.loc[mask]
    # print('ndf:')
    # print(ndf.head(n=5).to_string())
    """
    stream_sum = pd.to_timedelta('00:' + df["Song Length"]).sum()
    sum_conv = strfdelta(stream_sum, "{days} Tage, {hours} Stunden, {minutes} Minuten und {seconds} Sekunden")
    sum_text = f'(Ungefähre) Gesamte Hörzeit: {sum_conv}'
    sc_text = f'Anzahl Streams: {df.shape[0]}'
    days = strfdelta(stream_sum, "{days}")
    hours = strfdelta(stream_sum, "{hours}")
    minutes = strfdelta(stream_sum, "{minutes}")
    seconds = strfdelta(stream_sum, "{seconds}")

    tab = dbc.Table.from_dataframe(df.head(n=1000), striped=True, bordered=True, hover=True)

    return tab, sum_text, sc_text, days, hours, minutes, seconds

"""
df = dataframe_getter.get_top_album_df()
mask = dataframe_helpers.date_mask(start_date=start_date, end_date=end_date)
ndf = df.loc[mask]

# ndf = dataframe_helpers.get_top_albums(start_date=start_date, end_date=end_date)

all_albums_plot = px.bar(ndf.head(n=amount), x='Album', y="Stream Count", height=1000,  # markers=True,
                         title='Top Albums Streams',
                         color='Stream Count', color_continuous_scale=default_color_scale,
                         custom_data=['Album', 'Stream Count', 'Artist', 'Album-ID', 'Artist-ID'],
                         template=template_from_url(theme)
                         )

all_albums_plot.update_traces(
    hovertemplate="<br>".join([
        "Album: %{customdata[0]}",
        "Stream Count: %{customdata[1]}",
        "Artist: %{customdata[2]}",
        "Album-ID: %{customdata[3]}",
        "Artist-ID: %{customdata[4]}",
    ])
)

all_albums_plot.update_xaxes(showgrid=True, gridwidth=1,  # gridcolor='LightPink'
                             )
return all_albums_plot
"""
