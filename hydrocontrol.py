"""
set FLASK_APP=hydrocontrol
set FLASK_ENV=development
flask run

export FLASK_APP=hydrocontrol
fask run
"""
from multiprocessing import Process, Queue
import json
from flask import Flask, render_template, request, url_for, flash, redirect
from werkzeug.exceptions import abort

import controller


data = {
    "Light 1": {
        "On": dict(value="06:00", attrs='type=time required'),
        "Off": dict(value="18:00", attrs='type=time required')
    },
    "Light 2": {
        "On": dict(value="06:00", attrs='type=time required'),
        "Off": dict(value="18:00", attrs='type=time required')
    },
    "Fan": {
        "On": dict(value="00:00", attrs='type=time required'),
        "Off": dict(value="23:59", attrs='type=time required'),
        "Every": dict(value=10, attrs='type=number min=15 max=120'),
        "For": dict(value=1, attrs='type=number min=1 max=15')
    },
    "Heater": {
        "On": dict(value="00:00", attrs='type=time required'),
        "Off": dict(value="23:59", attrs='type=time required'),
        "Every": dict(value=15, attrs='type=number min=30 max=240'),
        "For": dict(value=2, attrs='type=number min=15 max=240')
    },
    "Air": {
        "On": dict(value="00:00", attrs='type=time required'),
        "Off": dict(value="23:59", attrs='type=time required'),
        "Every": dict(value=5, attrs='type=number min=1 max=60'),
        "For": dict(value=1, attrs='type=number min=1 max=60')
    },
}
with open("config.json", "w") as fh:
    json.dump(data, fh, indent=4)

qw, qr = Queue(), Queue()
p = Process(target=controller.main, args=(qw, qr))
p.start()

app = Flask(__name__)

@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        for name in request.form:
            print(name)
            key, subkey = name.split("_", 1)
            data[key][subkey]["value"] = request.form[name]
        with open("config.json", "w") as fh:
            json.dump(data, fh, indent=4)
        print(data)
        qw.put(controller.command_reload)
    return render_template('index.html', datadict=data)


@app.route('/query', methods=('GET',))
def query():
    qw.put(controller.command_get)
    rval = qr.get()
    return(str(rval))
