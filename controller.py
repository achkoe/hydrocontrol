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


class FakeClock():
    def __init__(self):
        self.tlist = []
        for day in [1, 2]:
            for hour in range(0, 24):
                for minute in range(0, 60):
                    for second in range(0, 60):
                        self.tlist.append(datetime(hour=hour, minute=minute, second=second, day=day, year=2001, month=1))
        self.cnt = 0

    def get(self):
        rval = self.tlist[self.cnt].replace(day=1, month=1, year=2001)
        self.cnt += 1
        return rval


#clock = FakeClock()
clock = Clock()


def tstr2datetime(s):
    now = clock.get()
    hms = dict(hour=0, minute=0, second=0, microsecond=0)
    hms.update(dict(zip(["hour", "minute", "second"], [int(item) for item in s.split(":")])))
    return now.replace(**hms)


def loop(timelist, queue_r, queue_w):
    while True:

        currenttime = clock.get()
        gpio_dict = dict([key, OFF] for key in gpio_map)
        for timeitem in timelist:
            time_on = tstr2datetime(timeitem["On"])
            time_off = tstr2datetime(timeitem["Off"])
            if currenttime >= time_on and currenttime < time_off:
                for key in gpio_dict:
                    if timeitem.get(key, False) is True:
                        gpio_dict[key] = ON

        if not queue_r.empty():
            cmd = queue_r.get()
            if cmd == command_reload:
                break
            elif cmd == command_get:
                rval = json.dumps(dict(timelist=timelist, state=gpio_dict))
                queue_w.put(rval)

        # print(currenttime, gpio_dict)
        for key in gpio_dict:
            GPIO.output(gpio_map[key], GPIO.HIGH if gpio_dict[key] is False else GPIO.LOW)

        # while clock.get().minute == currenttime.minute:
        #     pass
        time.sleep(0.1)


def main(queue_r, queue_w):
    GPIO.setmode(GPIO.BCM)
    for gpio in gpio_map.values():
        GPIO.setup(gpio, GPIO.OUT)

    while True:
        with open(config_name, "r") as fh:
            config = json.load(fh)
        loop(config, queue_r, queue_w)


if __name__ == '__main__':
    from multiprocessing import Queue

    with open(config_name, "r") as fh:
        config = json.load(fh)

    qw, qr = Queue(), Queue()
    loop(config, qr, qw)
