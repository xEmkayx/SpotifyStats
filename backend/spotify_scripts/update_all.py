from backend.spotify_scripts.BigOperations import utf8_albums
from backend.spotify_scripts.BigOperations import utf8_song_titles
from backend.spotify_scripts.BigOperations import update_artists


def main():
    utf8_albums.main()
    update_artists.main()
    utf8_song_titles.main()


if __name__ == '__main__':
    main()
