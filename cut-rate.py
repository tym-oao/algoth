#!/usr/bin/env python
# coding: utf-8

from flask import Flask, render_template, make_response, request
from flask_restful import Resource, Api, reqparse
import json
import os
from datetime import datetime

# Instantiate app
app = Flask(__name__)
api = Api(app)

# Load JSON message store if available
# (saved to a volume, preserves status across restarts)
try:
    QUEUE = json.load(open('/cache/queue.json', 'rt'))
except (ValueError, FileNotFoundError):
    QUEUE = {}

# Flask-RESTful reqparse boilerplate
parser = reqparse.RequestParser()
parser.add_argument('nickname')
parser.add_argument('status')
parser.add_argument('token')
parser.add_argument('color')

# set token value in order to validate posts

secret = os.getenv('TOKEN')
if not secret:
    with open('/secret/env', 'rt') as s:
        for line in s.readlines():
            if 'STATUSTOKEN' in line:
                secret = line.split('=')[1]


# API Classes
# Post to add a status, or get to fetch the entire message queue
class StatusMain(Resource):
    def post(self):
        args = parser.parse_args()
        nick = args['nickname']
        status = args['status']
        token = args['token']
        color = args['color']
        stamp = str(datetime.now())
        if (token == secret) or (secret is None):  # check that token is valid
            content = {'nickname': nick,
                       'status': status,
                       'color': color,
                       'at': stamp,
                       'client_ip': request.remote_addr}
            QUEUE[nick] = content
            with open('/cache/queue.json', 'wt') as fh:
                json.dump(QUEUE, fh)
            return QUEUE, 201
        else:
            return 'invalid token', 403

    def get(self):
        lst = []
        for item in QUEUE.values():
            lst.append(item)
        return lst, 200


class StatusNick(Resource):
    def post(self, nickname):
        args = parser.parse_args()
        status = args['status']
        token = args['token']
        color = args['color']
        stamp = str(datetime.now())
        if token == secret:  # check that token is valid
            content = {'nickname': nickname,
                       'status': status,
                       'color': color,
                       'at': stamp,
                       'client_ip': request.remote_addr}
            QUEUE[nickname] = content
            with open('/cache/queue.json', 'wt') as fh:
                json.dump(QUEUE, fh)
            return QUEUE[nickname], 201
        else:
            return 'invalid token! mine:%s yours:%s' % (secret, token), 403

    def get(self, nickname):
        try:
            return QUEUE[nickname], 201
        except KeyError:
            no_status = {'nickname': nickname, 'status': 'No such handle'}
            return no_status, 200

    def delete(self, nickname):
        QUEUE.pop(nickname, None)
        with open('/cache/queue.json', 'wt') as fh:
            json.dump(QUEUE, fh)
        return '', 204

# Flask-RESTful Endpoint routing
api.add_resource(StatusMain,
                 '/'
                 )
api.add_resource(StatusNick,
                 '/<nickname>')


# Little web UI
# Log monitor page
@app.route('/view')
def index():
    freight = render_template('statuslist.html', queue=QUEUE)
    v = make_response(freight)
    return v

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
