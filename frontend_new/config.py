import os
from pathlib import Path

DB_DIALECT = os.getenv("DB_DIALECT", "mysql")  # 'mysql' oder 'postgres'
CACHE_TIMEOUT_SEC = int(os.getenv("CACHE_TIMEOUT_SEC", "900"))  # 15 min
CACHE_DIR = os.getenv("CACHE_DIR", str(Path(__file__).resolve().parent / ".cache"))
# Wie oft (Sekunden) geprüft wird, ob neue Streams in der DB liegen
DATA_VERSION_TTL_SEC = int(os.getenv("DATA_VERSION_TTL_SEC", "60"))
BOOTSTRAP_THEME = "MORPH"  # andere: MINTY, MORPH, etc.

# Webserver (lokal: python -m frontend_new.app, im Container: gunicorn)
DASH_HOST = os.getenv("DASH_HOST", "127.0.0.1")
DASH_PORT = int(os.getenv("DASH_PORT", "8050"))
DASH_DEBUG = os.getenv("DASH_DEBUG", "false").lower() == "true"
