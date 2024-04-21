from datetime import datetime, timedelta


def ms_to_timestring(ms: int) -> str:
    millis = int(ms)
    seconds = (millis / 1000) % 60
    seconds = int(seconds)
    if seconds in range(0, 10):
        seconds = f'0{seconds}'
    minutes = (millis / (1000 * 60)) % 60
    minutes = int(minutes)
    if minutes in range(0, 9):
        minutes = f'0{minutes}'
    # hours = (millis / (1000 * 60 * 60)) % 24
    return f'{minutes}:{seconds}'
    # return f'{hours}:{minutes}:{seconds}'


def time_no_zero_s_to_timestring(time: str) -> str:
    t = time.split(':')
    mins = t[0]
    secs = t[1]
    if secs == 0:
        return f'{mins}:00'


def time_no_zero_mins_to_timestring(time: str) -> str:
    t = time.split(':')
    mins = t[0]
    secs = t[1]
    if mins in range(0, 10):
        mins = f'0{mins}'
    return f'0{mins}:{secs}'


def add_hours_to_dt(dt: datetime, hours: int) -> datetime:
    return dt + timedelta(hours=hours)


def ms_to_s(ms: int):
    return ms / 1000
