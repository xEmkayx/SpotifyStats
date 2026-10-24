"""
    Logisches Backup der Datenbank als gzip-SQL (Ersatz für mysqldump).

    Aufruf (aus dem Repo-Root):
        python -m db.backup_db [zielordner]

    Liest in einem konsistenten InnoDB-Snapshot, schreibt CREATE TABLE + INSERTs
    und prüft am Ende, ob die Zeilenzahlen pro Tabelle stimmen.
    Wiederherstellen:  gunzip -c <datei>.sql.gz | mysql -u <user> -p <datenbank>
"""
import gzip
import sys
from datetime import datetime
from pathlib import Path

from pymysql.converters import escape_item
from sqlalchemy import create_engine

from common.config.config import MYSQL_URL, MYSQL_DATABASE

BATCH = 1000


def backup(target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    out = target_dir / f"{MYSQL_DATABASE}_{datetime.now():%Y-%m-%d_%H%M%S}.sql.gz"
    conn = create_engine(MYSQL_URL).raw_connection()
    counts = {}
    try:
        cur = conn.cursor()
        cur.execute("SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        cur.execute("START TRANSACTION WITH CONSISTENT SNAPSHOT")
        cur.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
        tables = [r[0] for r in cur.fetchall()]
        with gzip.open(out, "wt", encoding="utf-8") as f:
            f.write(f"-- Backup {MYSQL_DATABASE} {datetime.now().isoformat()}\n")
            f.write("SET NAMES utf8mb4;\nSET FOREIGN_KEY_CHECKS=0;\n\n")
            for table in tables:
                cur.execute(f"SHOW CREATE TABLE `{table}`")
                f.write(f"DROP TABLE IF EXISTS `{table}`;\n{cur.fetchone()[1]};\n\n")
                cur.execute(f"SELECT * FROM `{table}`")
                cols = ", ".join(f"`{d[0]}`" for d in cur.description)
                n = 0
                while rows := cur.fetchmany(BATCH):
                    values = ",\n".join("(" + ", ".join(escape_item(v, "utf8mb4") for v in row) + ")" for row in rows)
                    f.write(f"INSERT INTO `{table}` ({cols}) VALUES\n{values};\n")
                    n += len(rows)
                counts[table] = n
                f.write("\n")
                print(f"{table}: {n} Zeilen")
            f.write("SET FOREIGN_KEY_CHECKS=1;\n")
        # Gegenprobe im selben Snapshot
        for table, n in counts.items():
            cur.execute(f"SELECT COUNT(*) FROM `{table}`")
            if cur.fetchone()[0] != n:
                raise RuntimeError(f"Zeilenzahl für {table} stimmt nicht")
        conn.rollback()
    finally:
        conn.close()
    return out


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "backups"
    path = backup(target)
    print(f"Backup geschrieben: {path} ({path.stat().st_size / 1e6:.1f} MB)")
