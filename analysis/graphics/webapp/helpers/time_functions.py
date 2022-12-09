from datetime import date, datetime, timedelta


def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)


def get_7days():
    delta = timedelta(days=7)
    days_ago = datetime.now() - delta
    start_date = f'{days_ago.year}-{days_ago.month}-{days_ago.day}'
    end_date = str(date(datetime.now().year, datetime.now().month, datetime.now().day + 1))
    print(f'7d - {start_date}, {end_date}')
    return start_date, end_date


def get_last_month():
    delta = timedelta(days=31)
    days_ago = datetime.now() - delta
    start_date = f'{days_ago.year}-{days_ago.month}-{days_ago.day}'
    end_date = str(date(datetime.now().year, datetime.now().month, datetime.now().day + 1))
    print(f'month - {start_date}, {end_date}')

    return start_date, end_date


def get_last_year():
    delta = timedelta(days=365)
    days_ago = datetime.now() - delta
    start_date = f'{days_ago.year}-{days_ago.month}-{days_ago.day}'
    end_date = str(date(datetime.now().year, datetime.now().month, datetime.now().day + 1))

    print(f'year - {start_date}, {end_date}')
    return start_date, end_date


def get_standard_time():
    start_date = f'{datetime.now().year}-{datetime.now().month}-{datetime.now().day}'
    end_date = str(date(datetime.now().year, datetime.now().month, datetime.now().day + 1))

    return start_date, end_date
