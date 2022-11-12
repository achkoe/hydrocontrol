"""Web Server for Hydro Control

It is an application using Flask to edit, add and delete
the list of items where every item
contains the on time, the off time and what to switch on or off.

The item in ths list looks like this:

<on time> <off time> <light 1> <Light 2> <Fan> <Air> <Heater> <Res>

It is presented as :

<select> <on time> <off time> <light 1> <Light 2> <Fan> <Air> <Heater> <Res>

where the "select" field is used for delete or add actions.

===============================================
set FLASK_APP=hydrocontrol
set FLASK_ENV=development

FLASK_APP=hydrocontrol set FLASK_ENV=development flask run

flask --app hydrocontrol.py run --host=0.0.0.0
"""
from multiprocessing import Process, Queue
import json
import time
import copy
import logging
from flask import Flask, render_template, request, url_for, redirect

import controller


logging.getLogger('werkzeug').setLevel(logging.ERROR)

# load configuration file
with open("config.json", "r") as fh:
    data = json.load(fh)

# get the keys for which to display current state
keylist = [item for item in controller.gpio_map.keys()]

# set up communication queues and start controller process.
qw, qr = Queue(), Queue()
p = Process(target=controller.main, args=(qw, qr))
p.start()

app = Flask(__name__)


def get_dname_and_pos(name):
    """Extract position and dict name from name.
    name is a string <dict name>_<position>, e.g "Fan_1" or "Air_20".
    Returns tuple (<dict name>, <position>)
    """
    dname, pos = name.rsplit("_", 1)
    pos = int(pos)
    return dname, pos


def get_select_pos(request):
    """Return the first position for "select" in request object or -1 if no "select" in request.
    """
    for name in request.form:
        dname, pos = get_dname_and_pos(name)
        if dname == "select":
            return pos
            break
    return -1


def save():
    """Save data in config.json and put a reload command in input queue of controller.
    """
    with open("config.json", "w") as fh:
        json.dump(data, fh, indent=4)
        qw.put(controller.command_reload)


def debug():
    print("======= {} =======".format(time.time()))
    for _ in data: print(_)


@app.route('/', methods=('GET', 'POST'))
def index():
    """Return index page."""
    global data
    if request.method == 'POST':
        for pos in range(len(data)):
            # Reset all switch channels in data
            for key in data[pos].keys():
                if key in ["On", "Off"]:
                    continue
                data[pos][key] = False
        for name in request.form:
            dname, pos = get_dname_and_pos(name)
            if dname not in ["On", "Off", "select"]:
                # update switch channel
                data[pos][dname] = True
            elif dname == "select":
                # ignore select flag
                pass
            else:
                # update on or off time
                data[pos][dname] = request.form[name]
        save()
    return render_template('index.html', data=data, keylist=keylist)


@app.route('/query', methods=('GET',))
def query():
    """Function to called by xmlhttprequest
    Ask the controller for the current status of all switch channels and return it.
    """
    qw.put(controller.command_get)
    rval = qr.get()
    return(str(rval))


@app.route('/add', methods=('POST', ))
def add():
    """Function to add a new list item, either after "select" position or at end of list."""
    print("ADD")
    pos = get_select_pos(request)
    data.insert(pos, copy.deepcopy(data[pos]))
    save()
    return redirect(url_for('index'))


@app.route('/delete', methods=('GET', 'POST'))
def delete():
    """Delete "select" item from list."""
    print("DEL")
    pos = get_select_pos(request)
    if pos != -1:
        del data[pos]
    save()
    return redirect(url_for('index'))
