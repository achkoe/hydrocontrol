"""Controller script for plant grow station.

3.3V                  1   2  5V
GPIO2                 3   4  5V
GPIO3                 5   6  GND
GPIO4                 7   8  GPIO14  Light1
GND                   9  10  GPIO15  Light2
GPIO17  Plug3 (Air)  11  12  GPIO18  Plug4 (Heater)
GPIO27  Plug5 (Res)  13  14  GND
GPIO22               15  16  GPIO23  Fan
"""
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
command_get = "get"

OFF = False
ON = True


gpio_map = {
    "Light 1": 14,
    "Light 2": 15,
    "Fan": 23,
    "Heater": 18,
    "Air": 17,
    "Res": 22,
}


class Clock():
    def __init__(self):
        self.ts = time.time()

    def get(self):
        self.ts += 60
        return datetime.now().replace(day=1, month=1, year=2001, second=0, microsecond=0)
        return datetime.fromtimestamp(self.ts).replace(day=1, month=1, year=2001, second=0, microsecond=0)


clock = Clock()


def tstr2datetime(s):
    now = clock.get()
    hms = dict(hour=0, minute=0, second=0, microsecond=0)
    hms.update(dict(zip(["hour", "minute", "second"], [int(item) for item in s.split(":")])))
    return now.replace(**hms)


def setup(config):
    """Return a dict with all keys from config.
    Values are
    currentstate (bool): current state of the output attached to key
    index (int): -1
    t (list(datetime)): a list with all times to swich output attached to key. Only time is important.
    """
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


def loop(cdict, queue_r, queue_w):
    # get the next time for each entry
    currenttime = clock.get()
    # print(f"currenttime={currenttime}\n")
    for key in cdict:
        index, state = get_next_time(cdict[key]["t"], currenttime)
        cdict[key]["index"] = index
        cdict[key]["currentstate"] = state
        print("{key}: currentstate={cs}, next event at {ne}: switch to {ns}".format(
            key=key,
            cs=cdict[key]["currentstate"],
            ne=cdict[key]["t"][cdict[key]["index"]],
            ns=not cdict[key]["currentstate"]), flush=True)
        # set output to current state
        GPIO.output(gpio_map[key], GPIO.HIGH if cdict[key]["currentstate"] is False else GPIO.LOW)
    while True:
        if not queue_r.empty():
            cmd = queue_r.get()
            if cmd == command_reload:
                break
            elif cmd == command_get:
                rval = json.dumps(dict([(key, cdict[key]["currentstate"]) for key in cdict]))
                # rval = ",".join("{key}={state}".format(key=key, state=cdict[key]["currentstate"]) for key in cdict)
                queue_w.put(rval)
        for key in cdict:
            nexttime = cdict[key]["t"][cdict[key]["index"]]
            if currenttime == nexttime:
                cdict[key]["currentstate"] = not cdict[key]["currentstate"]
                cdict[key]["index"] = 0 if cdict[key]["index"] + 1 >= len(cdict[key]["t"]) else cdict[key]["index"] + 1
                print("{ct}:{key}:{s}".format(key=key, ct=currenttime, s=cdict[key]["currentstate"]), flush=True)
                # set output to current state
                GPIO.output(gpio_map[key], GPIO.HIGH if cdict[key]["currentstate"] is False else GPIO.LOW)
        time.sleep(0.1)
        currenttime = clock.get()


def main(queue_r, queue_w):
    GPIO.setmode(GPIO.BCM)
    for gpio in gpio_map.values():
        GPIO.setup(gpio, GPIO.OUT)

    while True:
        with open(config_name, "r") as fh:
            config = json.load(fh)
        assert config.keys() == gpio_map.keys()
        cdict = setup(config)
        loop(cdict, queue_r, queue_w)


if __name__ == '__main__':
    from multiprocessing import Queue

    with open(config_name, "r") as fh:
        config = json.load(fh)
    with open(config_name, "w") as fh:
        json.dump(config, fh, indent=4)

    q = Queue()
    cdict = setup(config)
    #pprint.pprint(cdict)
    loop(cdict, q)
