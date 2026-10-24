"""
    Vollständiger Katalog-Abgleich. Ersetzt die früheren utf8_*-Reparaturskripte:
    Namen werden direkt aus den Spotify-Daten übernommen (inkl. Unicode),
    dazu ISRC, Verfügbarkeit und Relinking.
"""
from backend import catalog_sync


def main():
    return catalog_sync.full_sync()


if __name__ == '__main__':
    main()
