#!/usr/bin/env python2

import os
import json
import time
import functools
import datetime as DT

from flask import Flask, session, request, redirect, url_for, abort
import suds

import zenrox

APP = Flask(__name__)
#APP.secret_key = os.urandom(24)
APP.secret_key = 'mybigsecret'

HTML = '''
<html>
<head>
<link rel="stylesheet" type="text/css" href="/static/fixed-data-table.min.css"></script>
</head>
<body>
<div id="root"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/2.1.1/jquery.min.js"></script>
<script type="text/javascript" src="/static/zenrox_bundle.js"></script>
</body>
</html>
'''

ACCTS = {}

def requires_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        username = session.get('username')
        if username not in ACCTS:
            session.pop('username', None)
            abort(401)
        return f(*args, **kwargs)
    return decorated

# NOTE: /static is magically handled by flask

@APP.route('/')
def get_home():
    return HTML

@APP.route('/account')
def get_account():
    if session.get('username') not in ACCTS:
        session.pop('username', None)
    return json.dumps({'username': session.get('username')})

@APP.route('/timesheet')
@requires_auth
def get_timesheet():
    args = request.args
    date, prevts, nextts = args['date'], bool(int(args['prev'])), bool(int(args['next']))
    weekdate = zenrox.weekstart(DT.datetime.strptime(date, '%Y-%m-%d').date())
    if prevts and nextts:
        assert False, "Cannot get previous and next TS at the same time"
    elif prevts:
        weekdate = zenrox.weekstart(weekdate - DT.timedelta(days=1))
    elif nextts:
        weekdate = zenrox.weekend(weekdate) + DT.timedelta(days=1)

    userid, auth, mobauth = ACCTS[session['username']]
    timesheet = zenrox.get_timesheet(auth, userid, weekdate)
    assignments = zenrox.get_assignments(auth, userid, weekdate)
    entries = {}
    edate = weekdate
    while edate <= zenrox.weekend(weekdate):
        entries[edate.strftime('%Y-%m-%d')] = {}
        edate += DT.timedelta(days=1)
    for entry in timesheet.entries.values():
        edatestr = entry.date.strftime('%Y-%m-%d')
        eaid = entry.assignment_id
        assert eaid not in entries[edatestr]
        entries[edatestr][eaid] = entry.time.seconds
    return json.dumps({
        'weekdate': weekdate.strftime('%Y-%m-%d'),
        'assignments': [
            { 'uid': asgn.uid, 'project': asgn.project_name, 'task': asgn.task_name }
            for asgn in assignments.values()
        ],
        'entries': entries,
    })

@APP.route('/login', methods=['POST'])
def do_login():
    username, password = request.form['username'], request.form['password']
    try:
        auth = zenrox.initapi(username=username, password=password)
        ACCTS[username] = auth
    except AssertionError:
        abort(401)
    except suds.WebFault:
        abort(401)
    # TODO: set cookie path so nobody else can steal it
    session['username'] = request.form['username']
    return ''

#@APP.route('/logout')
#def do_logout():
#    session.pop('username', None)
#    return redirect(url_for('get_home'))

if __name__ == '__main__':
    zenrox.init()
    APP.run(host='0.0.0.0', port=8000,
            debug=True, use_evalex=False, use_reloader=True, extra_files='zenrox_ui.js',
            threaded=True)
