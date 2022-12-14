import dash
from dash import html, dcc, callback, Input, Output
from analysis.graphics.webapp.select_statements import *
from analysis.graphics.webapp.helpers.colors import colors
from analysis.graphics.webapp.helpers.df_filenames import *
from analysis.graphics.webapp.helpers.consts import *
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url
import dash_bootstrap_components as dbc

dash.register_page(__name__)

df = pd.read_csv(fr'{df_common_path}\{fn_df_allrounder}.csv')

gr = df.groupby('Gespielt am').agg(
    {'Song-ID': 'first', 'Song': 'first', 'Künstler': ', '.join, 'Künstler-ID': ', '.join,
     'Album': 'first', 'Album-ID': 'first'})

gr = gr.reset_index()[::-1]

# counted = gr.value_counts('Song-ID').rename({1: 'Song-ID', 2: 'Anzahl Streams'}).sort_index().reset_index()
# counted.set_axis(['Song-ID', 'Anzahl Streams'], axis=1, inplace=True)

# rest = gr.reset_index().drop('Gespielt am', axis=1).drop_duplicates('Song-ID').sort_values('Song-ID')

# df_combined = pd.merge(counted, rest).sort_values('Anzahl Streams', ascending=False)

table = dbc.Table.from_dataframe(gr.head(n=1000), striped=True, bordered=True, hover=True)
layout = html.Div(
    [
        html.H1(
            ['Stream History']
        ),
        table,
    ]
)
