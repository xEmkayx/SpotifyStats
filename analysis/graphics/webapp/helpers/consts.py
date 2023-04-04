from datetime import date, datetime, timedelta

default_color_scale = 'tealrose'
color_scales = ['aggrnyl', 'agsunset',
                'blackbody', 'bluered', 'blues', 'blugrn', 'bluyl', 'brwnyl',
                'bugn', 'bupu', 'burg', 'burgyl',
                'cividis', 'darkmint', 'electric', 'emrld',
                'gnbu', 'greens', 'greys', 'hot', 'inferno',
                'jet', 'magenta', 'magma', 'mint',
                'orrd', 'oranges', 'oryel',
                'peach', 'pinkyl', 'plasma', 'plotly3', 'pubu', 'pubugn', 'purd', 'purp', 'purples', 'purpor',
                'rainbow', 'rdbu', 'rdpu', 'redor', 'reds',
                'sunset', 'sunsetdark', 'teal', 'tealgrn', 'turbo',
                'viridis', 'ylgn', 'ylgnbu', 'ylorbr', 'ylorrd',
                'algae', 'amp', 'deep', 'dense', 'gray', 'haline', 'ice',
                'matter', 'solar', 'speed', 'tempo', 'thermal', 'turbid',
                'armyrose', 'brbg', 'earth', 'fall', 'geyser',
                'prgn', 'piyg', 'picnic', 'portland', 'puor',
                'rdgy', 'rdylbu', 'rdylgn',
                'spectral', 'tealrose', 'temps', 'tropic',
                'balance', 'curl', 'delta', 'oxy', 'edge',
                'hsv', 'icefire', 'phase', 'twilight', 'mrybm', 'mygbm'
                ]

TOMORROW_DATE = date(datetime.now().year, datetime.now().month, datetime.now().day + 1)
