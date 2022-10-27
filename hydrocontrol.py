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


def get_dname_and_pos(name):
    dname, pos = name.rsplit("_", 1)
    pos = int(pos)
    return dname, pos


def get_select_pos(request):
    for name in request.form:
        dname, pos = get_dname_and_pos(name)
        if dname == "select":
            return pos
            break
    return -1


def save():
    with open("config.json", "w") as fh:
        json.dump(data, fh, indent=4)
        qw.put(controller.command_reload)


@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        for pos in range(len(data)):
            data[pos].update(dict([(key, False) for key in data[pos].keys() if key not in ["On", "Off"]]))
        for name in request.form:
            dname, pos = get_dname_and_pos(name)
            # print(name, request.form.get(name, None))
            if dname not in ["On", "Off", "select"]:
                data[pos].update({dname: True})
            elif dname == "select":
                pass
            else:
                data[pos].update({dname: request.form[name]})
        for _ in data: print(_)
        save()
    return render_template('index.html', data=data, keylist=keylist)


@app.route('/query', methods=('GET',))
def query():
    qw.put(controller.command_get)
    rval = qr.get()
    return(str(rval))


@app.route('/add', methods=('POST', ))
def add():
    print("ADD")
    pos = get_select_pos(request)
    data.insert(pos, data[pos])
    save()
    return redirect(url_for('index'))


@app.route('/delete', methods=('GET', 'POST'))
def delete():
    print("DEL")
    pos = get_select_pos(request)
    if pos != -1:
        del data[pos]
    save()
    return redirect(url_for('index'))
