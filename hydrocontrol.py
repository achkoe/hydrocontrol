"""
set FLASK_APP=hydrocontrol
set FLASK_ENV=development
flask run

flask --app hydrocontrol.py run --host=0.0.0.0
"""
from multiprocessing import Process, Queue
import json
from flask import Flask, render_template, request, url_for, flash, redirect
from werkzeug.exceptions import abort

import controller


with open("config.json", "r") as fh:
    data = json.load(fh)
keylist = [item for item in controller.gpio_map.keys()]

qw, qr = Queue(), Queue()
p = Process(target=controller.main, args=(qw, qr))
p.start()

app = Flask(__name__)

@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        with open("config.json", "w") as fh:
            json.dump(data, fh, indent=4)
        qw.put(controller.command_reload)
    fdata = "\n".join(f"{item!r}" for item in data)
    return render_template('index.html', data=fdata, keylist=keylist)
    #return render_template('index.html', data=json.dumps(data, indent=4), keylist=keylist)


@app.route('/query', methods=('GET',))
def query():
    qw.put(controller.command_get)
    rval = qr.get()
    return(str(rval))
