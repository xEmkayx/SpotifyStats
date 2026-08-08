import os

DB_URL = os.getenv("DB_URL", "mysql+pymysql://user:pass@localhost/spotify_stats?charset=utf8mb4")
DB_DIALECT = os.getenv("DB_DIALECT", "mysql")  # 'mysql' oder 'postgres'
CACHE_TIMEOUT_SEC = int(os.getenv("CACHE_TIMEOUT_SEC", "900"))  # 15 min
BOOTSTRAP_THEME = "MORPH"  # andere: MINTY, MORPH, etc.
