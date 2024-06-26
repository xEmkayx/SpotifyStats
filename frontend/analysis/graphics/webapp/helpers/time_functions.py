import time
from datetime import datetime, timedelta
from frontend.analysis.graphics.webapp.helpers.consts import TOMORROW_DATE


def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)


def get_7days():
    delta = timedelta(days=7)
    days_ago = datetime.now() - delta
    start_date = f'{days_ago.year}-{days_ago.month}-{days_ago.day}'
    end_date = str(TOMORROW_DATE)
    # print(f'7d - {start_date}, {end_date}')
    return start_date, end_date


def get_last_month():
    delta = timedelta(days=31)
    days_ago = datetime.now() - delta
    start_date = f'{days_ago.year}-{days_ago.month}-{days_ago.day}'
    end_date = str(TOMORROW_DATE)
    # print(f'month - {start_date}, {end_date}')

    return start_date, end_date


def get_last_year():
    delta = timedelta(days=365)
    days_ago = datetime.now() - delta
    start_date = f'{days_ago.year}-{days_ago.month}-{days_ago.day}'
    end_date = str(TOMORROW_DATE)

    # print(f'year - {start_date}, {end_date}')
    return start_date, end_date


def get_standard_time():
    start_date = f'{datetime.now().year}-{datetime.now().month}-{datetime.now().day}'
    end_date = str(TOMORROW_DATE)

    return start_date, end_date


def timestring_to_seconds(t: str):
    # print('timestring to seconds')
    # print(f'parameter: {t}')
    x = time.strptime(t.split(',')[0], '%H:%M:%S')
    # print(f'x:{x}\n')
    sec = timedelta(hours=x.tm_hour, minutes=x.tm_min, seconds=x.tm_sec).total_seconds()
    return sec
