import json
from traceback import format_exc

from auth import spotify_auth_manager
from common.config.important_values import *

logging.basicConfig(
    level=log_level,
    format=log_format,
    datefmt=log_datefmt,
    # filename=log_filename
)


def main():
    spotify = spotify_auth_manager.get_authenticated_spotify_client()

    if spotify is None:
        raise Exception("No valid token")

    last_streams = spotify.current_user_recently_played(limit=50)

    try:
        with open(last_streams_dir, 'w') as jf:
            jf.write(json.dumps(last_streams, indent=4))
        logging.info(f'Wrote to last_streams.json')
    except:
        logging.error(f'Error while writing file:\n{format_exc()}')


if __name__ == '__main__':
    main()
