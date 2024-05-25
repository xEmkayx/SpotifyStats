import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
# todo: check scopes
SCOPE = 'user-read-recently-played user-library-read user-read-private playlist-read-private ' \
        'playlist-read-collaborative user-top-read user-read-currently-playing playlist-modify-public playlist-modify-private'
TOKEN_CACHE_FILE_PATH = os.getenv('TOKEN_CACHE_FILE_PATH', default='/app/data/spotify_token_cache')
SPOTIFY_USERNAME = os.getenv('SPOTIFY_USERNAME')

# mysql
# MYSQL_ROOT_PASSWORD = os.getenv('MYSQL_ROOT_PASSWORD')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_HOST = os.getenv('MYSQL_HOST', default='db')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE',  default='spotify_stats')
