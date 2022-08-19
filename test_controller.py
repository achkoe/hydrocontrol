import datetime
import pytest
import controller

# tlist = [6:00, 12:00, 15:00, 18:00]
# currenttime = 5:00  -> index = 0, state = Off
# currenttime = 7:00  -> index = 1, state = On
# currenttime = 13:00 -> index = 2, state = Off
# currenttime = 17:00 -> index = 3, state = On
# currenttime = 19:00 -> index = 0, state = Off

tlist = [
    datetime.datetime(year=2001, month=1, day=1, hour=6, minute=0, second=0),
    datetime.datetime(year=2001, month=1, day=1, hour=12, minute=0, second=0),
    datetime.datetime(year=2001, month=1, day=1, hour=15, minute=0, second=0),
    datetime.datetime(year=2001, month=1, day=1, hour=18, minute=0, second=0),
]


@pytest.mark.parametrize(
    ("tlist", "t", "expected"),
    [
        pytest.param(tlist, datetime.datetime(year=2001, month=1, day=1, hour=5, minute=0, second=0), (0, False)),
        pytest.param(tlist, datetime.datetime(year=2001, month=1, day=1, hour=7, minute=0, second=0), (1, True)),
        pytest.param(tlist, datetime.datetime(year=2001, month=1, day=1, hour=13, minute=0, second=0), (2, False)),
        pytest.param(tlist, datetime.datetime(year=2001, month=1, day=1, hour=17, minute=0, second=0), (3, True)),
        pytest.param(tlist, datetime.datetime(year=2001, month=1, day=1, hour=19, minute=0, second=0), (0, False)),
    ])
def test_get_next_time(tlist, t, expected):
    index, state = controller.get_next_time(tlist, t)
    obtained = (index, state)
    assert expected == obtained, f"obtained {obtained!r}, expected {expected!r}"


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        pytest.param(
            dict(A=dict(On=dict(value="6:00"), Off=dict(value="18:00"))),
            dict(A=dict(
                t=[
                    datetime.datetime(year=2001, month=1, day=1, hour=6, minute=0),
                    datetime.datetime(year=2001, month=1, day=1, hour=18, minute=0)],
                index=-1,
                currentstate=False
            )),
            id="1"),
        pytest.param(
            dict(A=dict(On=dict(value="6:00"), Off=dict(value="17:00"), Every=dict(value=120), For=dict(value=5))),
            dict(A=dict(
                t=[
                    datetime.datetime(year=2001, month=1, day=1, hour=6, minute=0),
                    datetime.datetime(year=2001, month=1, day=1, hour=6, minute=5),
                    datetime.datetime(year=2001, month=1, day=1, hour=8, minute=0),
                    datetime.datetime(year=2001, month=1, day=1, hour=8, minute=5),
                    datetime.datetime(year=2001, month=1, day=1, hour=10, minute=0),
                    datetime.datetime(year=2001, month=1, day=1, hour=10, minute=5),
                    datetime.datetime(year=2001, month=1, day=1, hour=12, minute=0),
                    datetime.datetime(year=2001, month=1, day=1, hour=12, minute=5),
                    datetime.datetime(year=2001, month=1, day=1, hour=14, minute=0),
                    datetime.datetime(year=2001, month=1, day=1, hour=14, minute=5),
                    datetime.datetime(year=2001, month=1, day=1, hour=16, minute=0),
                    datetime.datetime(year=2001, month=1, day=1, hour=16, minute=5)],
                index=-1,
                currentstate=False
            )),
            id="1"),

    ])
def test_setup(config, expected):
    print(config)
    cdict = controller.setup(config)
    assert cdict == expected