from collections import namedtuple

BCM = "BCM"
OUT = "OUT"
HIGH = 1
LOW = 0


def setmode(mode):
    pass


def setup(n, s):
    pass


def output(n, s):
    pass
    #print(f"set {n} to {s}")


class _SMBus2():
    def __init__(self):
        pass

    def SMBus(self, port):
        pass


class _bme280():
    def load_calibration_params(self, bus, address):
        pass

    def sample(self, bus, address, calibrationParameters):
        nt = namedtuple("nt", ["temperature", "humidity", "pressure"])
        return nt(temperature=12.12, humidity=66.66, pressure=1066)


smbus2 = _SMBus2()
bme280 = _bme280()
