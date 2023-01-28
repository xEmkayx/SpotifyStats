class SongSummary:
    song_id: str
    song_name: str
    artist_name: str
    album_name: str
    song_image: str
    streamed_amount: int
    streamed_minutes: int

    def __init__(self, song_id, song_name, artist_name, album_name, song_image, streamed_amount, streamed_minutes):
        self.song_id = song_id
        self.song_name = song_name
        self.artist_name = artist_name
        self.album_name = album_name
        self.song_image = song_image
        self.streamed_amount = streamed_amount
        self.streamed_minutes = streamed_minutes


class ArtistSummary:
    artist_id: str
    artist_name: str
    artist_image: str
    streamed_amount: int = 0
    streamed_minutes: int = 0

    def __init__(self, artist_id, artist_name, artist_image, streamed_amount = 0, streamed_minutes = 0):
        self.artist_id = artist_id
        self.artist_name = artist_name
        self.artist_image = artist_image
        self.streamed_amount = streamed_amount
        self.streamed_minutes = streamed_minutes


class AlbumSummary:
    album_id: str
    album_name: str
    album_artist: str
    album_image: str
    streamed_amount: int = 0
    streamed_minutes: int = 0

    def __init__(self, album_id, album_name, album_artist, album_image, streamed_amount = 0, streamed_minutes = 0):
        self.album_id = album_id
        self.album_name = album_name
        self.album_artist = album_artist
        self.album_image = album_image
        self.streamed_amount = streamed_amount
        self.streamed_minutes = streamed_minutes
