import json
import time
from datetime import datetime, timedelta
import pprint

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    import fake_gpio as GPIO


config_name = "config.json"
command_reload = "reload"

OFF = False
ON = True


gpio_map = {
    "Light 1": 14,
    "Light 2": 15,
    "Fan": 17,
    "Heater": 18,
    "Air": 22,
}


def tstr2datetime(s):
    now = datetime.now().replace(day=1, month=1, year=2001)
    hms = dict(hour=0, minute=0, second=0, microsecond=0)
    hms.update(dict(zip(["hour", "minute", "second"], [int(item) for item in s.split(":")])))
    return now.replace(**hms)


def setup():
    """Reads config file and returns a dict with all keys from config.
    Values are
    currentstate (bool): current state of the output attached to key
    index (int): -1
    t (list(datetime)): a list with all times to swich output attached to key. Only time is important.
    """
    with open(config_name, "r") as fh:
        config = json.load(fh)

    assert config.keys() == gpio_map.keys()

    GPIO.setmode(GPIO.BCM)
    for gpio in gpio_map.values():
        GPIO.setup(gpio, GPIO.OUT)

    cdict = dict()
    for key in config:
        assert "On" in config[key]
        assert "Off" in config[key]
        cdict[key] = dict(t=[], index=-1, currentstate=OFF)
        if "Every" in config[key]:
            assert "For" in config[key]
            t_every = timedelta(seconds=60 * int(config[key]["Every"]["value"]))  # every is in minutes
            t_for = timedelta(seconds=60 * int(config[key]["For"]["value"]))     # for is in minutes
            t_start = tstr2datetime(config[key]["On"]["value"])
            t_stop = tstr2datetime(config[key]["Off"]["value"])
            while True:
                t_next = t_start + t_for
                cdict[key]["t"].append(t_start)
                cdict[key]["t"].append(t_next)
                t_start = t_start + t_every
                if t_start >= t_stop:
                    break
        else:
            cdict[key]["t"] = [tstr2datetime(config[key]["On"]["value"]), tstr2datetime(config[key]["Off"]["value"])]
    return cdict


def get_fake_time():
    now = datetime.now()
    now = now.replace(hour=19, minute=0, second=0, microsecond=0)
    te = now + timedelta(days=2)
    # print(now, te)
    tlist = []
    while now < te:
        now = now + timedelta(minutes=1)
        tlist.append(now.replace(day=1, month=1, year=2001))
    for t in tlist:
        yield t


def gettime():
    now = datetime.now()
    yield now.replace(day=1, month=1, year=2001)


def get_next_time(tlist, t):
    # tlist = [6:00, 12:00, 16:00, 18:00]
    # currenttime = 5:00  -> index = 0, state = Off
    # currenttime = 7:00  -> index = 1, state = On
    # currenttime = 13:00 -> index = 2, state = Off
    # currenttime = 17:00 -> index = 3, state = On
    # currenttime = 19:00 -> index = 0, state = Off
    state = OFF
    if t < tlist[0]:
        return 0, state
    elif t > tlist[-1]:
        return 0, state
    else:
        for index in range(len(tlist)):
            if t < tlist[index]:
                break
            state = not state
        return index, state


def loop(cdict, queue, timefn=gettime):
    # get the next time for each entry
    t = timefn()
    currenttime = next(t)
    print(f"currenttime={currenttime}\n")
    for key in cdict:
        index, state = get_next_time(cdict[key]["t"], currenttime)
        cdict[key]["index"] = index
        cdict[key]["currentstate"] = state
        print("{key}: currentstate={cs}, next event at {ne}: switch to {ns}".format(
            key=key,
            cs=cdict[key]["currentstate"],
            ne=cdict[key]["t"][cdict[key]["index"]],
            ns=not cdict[key]["currentstate"]))
        # set output to current state
        GPIO.output(gpio_map[key], GPIO.HIGH if cdict[key]["currentstate"] is False else GPIO.LOW)
    while True:
        if not queue.empty() and queue.get() == command_reload:
            break
        for key in cdict:
            nexttime = cdict[key]["t"][cdict[key]["index"]]
            if currenttime == nexttime:
                cdict[key]["currentstate"] = not cdict[key]["currentstate"]
                cdict[key]["index"] = 0 if cdict[key]["index"] + 1 >= len(cdict[key]["t"]) else cdict[key]["index"] + 1
                print("{ct}: {key} switch to {s}".format(key=key, ct=currenttime, s=cdict[key]["currentstate"]))
                # set output to current state
                GPIO.output(gpio_map[key], GPIO.HIGH if cdict[key]["currentstate"] is False else GPIO.LOW)
        time.sleep(0.1)
        currenttime = next(t)


def main(queue):
    while True:
        cdict = setup()
        loop(cdict, queue)


if __name__ == '__main__':
    from multiprocessing import Queue

    with open(config_name, "r") as fh:
        d = json.load(fh)
    with open(config_name, "w") as fh:
        json.dump(d, fh, indent=4)

    q = Queue()
    cdict = setup()
    pprint.pprint(cdict)
    loop(cdict, q, timefn=get_fake_time)
