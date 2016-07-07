
import re
from os import environ
from uuid import uuid4

import redis
import requests
from flask import Flask, json, jsonify, render_template, request

application = app = Flask(__name__)

client_id = environ['SLACK_CLIENT_ID']
client_secret = environ['SLACK_CLIENT_SECRET']
# verification_token = environ['SLACK_VERIFICATION_TOKEN']

db = redis.StrictRedis(host=environ.get('REDIS_HOST', 'localhost'))


@app.route('/')
def index():
    return render_template('index.html', client_id=client_id)


@app.route('/oauth')
def oauth():
    code = request.args['code']
    requests.post('https://slack.com/api/oauth.access', data={
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
    })
    return render_template('index.html', auth_done=True)


spoiler_pat = re.compile(r'\{(.+?)\}')


def hide_spoiler(m):
    if m:
        return '\xe2\x96\x88'.decode('utf-8') * len(m.group(1))
    else:
        ''


def show_spoiler(m):
    if m:
        return m.group(1)
    else:
        ''


@app.route('/command', methods=['POST'])
def command():
    user_name = request.form['user_name']
    callback_id = str(uuid4())
    text = request.form['text']

    message = {
        'text': None,
        'color': '#000000',
        'attachments': [
            {
                'text': spoiler_pat.sub(hide_spoiler, text),
                'author_name': user_name,
                'callback_id': callback_id,
                'actions': [
                    {
                        'name': 'show_spoiler',
                        'text': 'Show spoiler',
                        'type': 'button',
                        'confirm': {
                            'title': user_name,
                            'text': spoiler_pat.sub(show_spoiler, text),
                        },
                    }
                ],
            },
        ],
    }
    db.set('spoilers:{}'.format(callback_id), json.dumps(message))

    message.update(response_type='in_channel')
    requests.post(request.form['response_url'], json=message)

    return ""


@app.route('/interact', methods=['POST'])
def interact():
    data = json.loads(request.form['payload'])
    callback_id = data['callback_id']
    message = json.loads(db.get('spoilers:' + callback_id))
    views = db.incr('spoiler_views:' + callback_id)
    message['attachments'][0]['footer'] = '{} viewed this spoiler'.format(views)
    message.update(replace_original=True)
    return jsonify(message)


if __name__ == '__main__':
    app.run(debug=True)

