import dash
import pandas as pd
import plotly.express as px
from dash import html, dcc, callback, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

from analysis.graphics.webapp.components.selection_box import SelectionBox, B7D_NAME, BMONTH_NAME, BYEAR_NAME
from analysis.graphics.webapp.df_files import ndf_helper
from analysis.graphics.webapp.helpers.time_functions import *
import dash_bootstrap_components as dbc
from analysis.graphics.webapp.helpers import dataframe_helpers, name_helpers
from analysis.graphics.webapp.helpers.consts import *

dash.register_page(__name__)

# df = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')
# df = dataframe_loader.get_default_dataframe()

theme_change = ThemeChangerAIO(aio_id="theme")

graph = dcc.Graph(
    id='all-artists-line',
    # figure=all_artists_plot
)

sb = SelectionBox(name_helpers.get_current_file_name(__file__))
datepicker_id = sb.get_datepicker_id()
b_ids = sb.get_buttons_ids()
b7d_id = b_ids[B7D_NAME]
bmonth_id = b_ids[BMONTH_NAME]
byear_id = b_ids[BYEAR_NAME]
input_id = sb.get_input_id()

layout = html.Div(children=[
    html.H1(children='All Artist Streams'),
    sb.render(),
    dcc.Loading(
        id='load-top-artists',
        children=[graph],
    ),
    # theme_change
])


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
    Output("all-artists-line", "figure"),

    Input(DATAFRAME_STORE_ID, 'data'),
    Input(datepicker_id, 'start_date'),
    Input(datepicker_id, 'end_date'),
    Input(ThemeChangerAIO.ids.radio("all-themes"), "value"),
    Input(input_id, 'value')
)
def update_graph_theme(df_store, start_date, end_date, theme, amount):
    df = pd.DataFrame(df_store)
    ndf = ndf_helper.get_top_songs_df(df, start_date=start_date, end_date=end_date)
    # df = dataframe_getter.get_top_artist_df()
    # mask = dataframe_helpers.date_mask(start_date=start_date, end_date=end_date)
    # ndf = df.loc[mask]

    fig = px.bar(ndf.head(n=amount), x='Artist', y="Stream Count", height=1000,
                 title='Top Artist Streams',
                 color='Stream Count', color_continuous_scale=default_color_scale,
                 custom_data=['Artist', 'Stream Count', 'Artist-ID'],
                 template=template_from_url(theme)
                 )
    """
    # fig = px.line(df_sorted.head(n=500), x="Artist", y="Stream Count", template=template_from_url(theme),
    fig = px.line(ndf.head(n=250), x="Artist", y="Stream Count", template=template_from_url(theme),
                  markers=True, height=1000,
                  title=f'Streamzahlen aller Artist"',
                  custom_data=['Artist', 'Stream Count', 'Artist-ID'])
    """

    fig.update_traces(
        hovertemplate="<br>".join([
            "Artist: %{customdata[0]}",
            "Stream Count: %{customdata[1]}",
            "Artist-ID: %{customdata[2]}",
        ])
    )
    return fig
