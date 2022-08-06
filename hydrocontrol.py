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


q = Queue()
p = Process(target=controller.main, args=(q, ))
p.start()
q.put(controller.command_reload)


app = Flask(__name__)

data = {
    "Light 1": {
        "On": dict(value="06:00", attrs='type=time required'),
        "Off": dict(value="18:00", attrs='type=time required')
    },
    "Light 2": {
        "On": dict(value="06:00", attrs='type=time required'),
        "Off": dict(value="18:00", attrs='type=time required')
    },
    "Air": {
        "On": dict(value="00:00", attrs='type=time required'),
        "Off": dict(value="23:59", attrs='type=time required'),
        "Every": dict(value=30, attrs='type=number min=15 max=60'),
        "For": dict(value=5, attrs='type=number min=5 max=15')
    },
    "Fan": {
        "On": dict(value="00:00", attrs='type=time required'),
        "Off": dict(value="23:59", attrs='type=time required'),
        "Every": dict(value=60, attrs='type=number min=15 max=60'),
        "For": dict(value=1, attrs='type=number min=1 max=15')
    },
    "Heater": {
        "On": dict(value="00:00", attrs='type=time required'),
        "Off": dict(value="23:59", attrs='type=time required'),
        "Every": dict(value=120, attrs='type=number min=30 max=240'),
        "For": dict(value=30, attrs='type=number min=15 max=120')
    }
}


@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        for name in request.form:
            key, subkey = name.split("_", 1)
            # print(key, subkey, request.form[name])
            data[key][subkey]["value"] = request.form[name]
        with open("config.json", "w") as fh:
            json.dump(data, fh)
        q.put(controller.command_reload)
    return render_template('index.html', datadict=data)
