from flask import Flask
from flask_caching import Cache

from frontend_new.config import CACHE_DIR

cache = Cache()

def init_extensions(server: Flask, cache_timeout_sec: int=900):
    # FileSystemCache wird von allen gunicorn-Workern geteilt
    cache.init_app(server, config={
        'CACHE_TYPE': 'FileSystemCache',
        'CACHE_DIR': CACHE_DIR,
        'CACHE_DEFAULT_TIMEOUT': cache_timeout_sec,
        'CACHE_THRESHOLD': 5000,
    })
