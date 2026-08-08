from dash import html
import dash_bootstrap_components as dbc

PBTN_TYPE = "playlist-btn"
PMODAL_TYPE = "playlist-modal"
PNAME_TYPE = "playlist-name"
PPUBLIC_TYPE = "playlist-public"
PCONFIRM_TYPE = "playlist-confirm"
PSTATUS_TYPE = "playlist-status"

def pbtn(scope):       return {"type": PBTN_TYPE, "scope": scope}
def pmodal(scope):     return {"type": PMODAL_TYPE, "scope": scope}
def pname(scope):      return {"type": PNAME_TYPE, "scope": scope}
def ppublic(scope):    return {"type": PPUBLIC_TYPE, "scope": scope}
def pconfirm(scope):   return {"type": PCONFIRM_TYPE, "scope": scope}
def pstatus(scope):    return {"type": PSTATUS_TYPE, "scope": scope}

def playlist_button(scope: str, label="Als Playlist speichern"):
    return dbc.Button([html.I(className="bi bi-spotify me-1"), label],
    id=pbtn(scope), color="success", outline=True, size="sm")

def playlist_modal(scope: str, default_name="SpotifyStats Playlist"):
    return dbc.Modal(
    id=pmodal(scope),
    is_open=False,
    children=[
    dbc.ModalHeader(dbc.ModalTitle("Playlist erstellen")),
    dbc.ModalBody([
    dbc.Label("Name"),
    dbc.Input(id=pname(scope), value=default_name, placeholder="Playlist-Name", type="text"),
    html.Br(),
    dbc.Checkbox(id=ppublic(scope), value=True, label="Öffentliche Playlist"),
    html.Div(className="text-muted mt-2",
    children="Die Playlist enthält die aktuell angezeigten Top-Songs in der gewählten Reihenfolge.")
    ]),
    dbc.ModalFooter([
    dbc.Button("Abbrechen", id={"type":"modal-cancel","scope":scope}, color="secondary", outline=True),
    dbc.Button("Erstellen", id=pconfirm(scope), color="success")
    ])
    ],
    backdrop=True, keyboard=True, centered=True
    )


def playlist_status(scope: str):
    return html.Div(id=pstatus(scope))
