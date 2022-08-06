import json
import time
from datetime import datetime, timedelta
import pprint


config_name = "config.json"
command_reload = "reload"

OFF = False
ON = True


def load_config():
    with open(config_name, "r") as fh:
        return json.load(fh)


def control(queue):
    while 1:
        if not queue.empty():
            command = queue.get()
            if command == command_reload:
                config = load_config()
                print(config)
        time.sleep(1)


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
    now = now.replace(hour=5, minute=0, second=0, microsecond=0)
    te = now + timedelta(days=2)
    print(now, te)
    tlist = []
    while now < te:
        now = now + timedelta(minutes=1)
        tlist.append(now.replace(day=1, month=1, year=2001))
    for t in tlist:
        yield t


def gettime():
    now = datetime.now()
    return now.replace(day=1, month=1, year=2001)


def loop(cdict, queue, debug=False):
    # get the next time for each entry
    if debug:
        t = get_fake_time()
        currenttime = next(t)
    else:
        currenttime = gettime()
    for key in cdict:
        state = cdict[key]["currentstate"]
        for index in range(len(cdict[key]["t"])):
            if currenttime < cdict[key]["t"][index]:
                cdict[key]["index"] = index
                cdict[key]["currentstate"] = state
                # TODO: set output to current state
                break
            state = not state
        print("{key}: current time {ct}\ncurrentstate={cs}, next event at {ne}: switch to {ns}".format(
            key=key,
            ct=currenttime,
            cs=cdict[key]["currentstate"],
            ne=cdict[key]["t"][cdict[key]["index"]],
            ns=not cdict[key]["currentstate"]))
    while True:
        if not queue.empty() and queue.get() == command_reload:
            break
        for key in cdict:
            nexttime = cdict[key]["t"][cdict[key]["index"]]
            if currenttime == nexttime:
                cdict[key]["currentstate"] = not cdict[key]["currentstate"]
                cdict[key]["index"] = 0 if cdict[key]["index"] + 1 >= len(cdict[key]["t"]) else cdict[key]["index"] + 1
                print("{ct}: {key} switch to {s}".format(key=key, ct=currenttime, s=cdict[key]["currentstate"]))
        if debug:
            currenttime = next(t)
        else:
            time.sleep(1)
            currenttime = gettime()


def main(queue):
    while True:
        cdict = setup()
        loop(cdict, queue)


if __name__ == '__main__':
    from multiprocessing import Queue

    q = Queue()
    cdict = setup()
    pprint.pprint(cdict)
    #loop(cdict, q, debug=True)
