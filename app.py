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


@app.route('/command', methods=['POST'])
def command():
    text_match = re.match(r'(?:\[(?P<topic>.*)\])?\s*(?P<spoiler>.*)',
                          request.form['text'])
    spoiler = text_match.group('spoiler')
    topic = text_match.group('topic')

    if topic is None:
        topic = 'Spoiler alert!'

    callback_id = uuid4()
    db.set('spoilers:{}'.format(callback_id), spoiler)

    requests.post(request.form['response_url'], json={
        'response_type': 'in_channel',
        'text': '*{}*: {}'.format(request.form['user_name'], topic),
        'attachments': [
            {
                'text': None,
                'fallback': None,
                'callback_id': callback_id,
                'actions': [
                    {
                        'name': 'show_spoiler',
                        'text': 'Show spoiler',
                        'type': 'button',
                    }
                ],
            }
        ],
    })

    return ""


@app.route('/interact', methods=['POST'])
def interact():
    data = json.loads(request.form['payload'])
    spoiler = db.get('spoilers:' + data['callback_id'])
    return jsonify({
        'text': spoiler,
        'response_type': 'ephemeral',
        'replace_original': False,
    })


if __name__ == '__main__':
    app.run(debug=True)

