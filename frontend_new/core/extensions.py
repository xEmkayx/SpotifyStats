from flask import Flask
from flask_caching import Cache

cache = Cache()

def init_extensions(server: Flask, cache_timeout_sec: int=900):
    cache.init_app(server, config={
        'CACHE_TYPE': 'FileSystemCache',
        'CACHE_DIR': './.cache',
        'CACHE_DEFAULT_TIMEOUT': cache_timeout_sec,
    })
