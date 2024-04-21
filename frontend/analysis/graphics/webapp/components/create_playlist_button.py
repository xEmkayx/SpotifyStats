import dash_bootstrap_components as dbc


class CreatePlaylistButton:
    def __init__(self, page_name):
        self.page_name = page_name
        self.id = f"playlist-button-{self.page_name}"

    def get_id(self):
        return self.id

    def render(self):
        return dbc.Button(
            'Create a Playlist from these Songs',
            id=self.id,
            # outline=True,
            color='success',
            n_clicks=0,
            className='create-playlist-button'
        )
