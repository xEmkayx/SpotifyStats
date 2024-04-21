#!/usr/bin/python3.10

from backend.spotify_scripts import last_streamed_to_file, last_streamed_to_db


def main():
    last_streamed_to_file.main()
    last_streamed_to_db.main()


if __name__ == '__main__':
    main()
