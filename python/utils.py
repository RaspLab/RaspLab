import time, requests, threading, os, json
from datetime import datetime


def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    from datetime import datetime
    now = datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time, datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "qualche istante fa"
        if second_diff < 60:
            return str(second_diff) + " secondi fa"
        if second_diff < 120:
            return "un minuto fa"
        if second_diff < 3600:
            return str(second_diff // 60) + " minuti fa"
        if second_diff < 7200:
            return "un'ora fa"
        if second_diff < 86400:
            return str(second_diff // 3600) + " ore fa"
    if day_diff == 1:
        return "ieri"
    if day_diff < 7:
        return str(day_diff) + " giorni fa"
    if day_diff < 31:
        return str(day_diff // 7) + " settimane fa"
    if day_diff < 365:
        return str(day_diff // 30) + " mesi fa"
    return str(day_diff // 365) + " anni fa"


def start_runner():
    def start_loop():
        not_started = True
        while not_started:
            try:
                r = requests.get('http://127.0.0.1:5000/')
                if r.status_code == 200:
                    not_started = False
            except:
                pass
            time.sleep(2)

    thread = threading.Thread(target=start_loop)
    thread.start()


def real_path(path):
    dir = os.path.dirname(__file__)
    return os.path.join(dir, path)


def save_info(settings, cache):
    open(real_path("common/settings.json"), "w").write(json.dumps(settings))
    open(real_path("common/cache.json"), "w").write(json.dumps(cache))


def bring_down_state(context, settings, cache):
    context['state'] = 0
    save_info(settings, cache)


def update_time(settings, cache, context):
    now = int(datetime.now().timestamp())
    cache['last_update'] = now
    context['last_update'] = now
    save_info(settings, cache)
