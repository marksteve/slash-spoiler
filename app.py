from os import environ
from urllib import urlencode
from uuid import uuid4

import requests
from flask import Flask, json, jsonify, redirect, request

application = app = Flask(__name__)
client_id = environ['SLACK_CLIENT_ID']
client_secret = environ['SLACK_CLIENT_SECRET']
# verification_token = environ['SLACK_VERIFICATION_TOKEN']

tokens = {}
spoilers = {}


@app.route('/auth')
def auth():
    return redirect('https://slack.com/oauth/authorize?{}'.format(urlencode({
        'client_id': client_id,
        'scope': 'commands chat:write:user',
    })))


@app.route('/oauth')
def oauth():
    code = request.args['code']
    r = requests.post('https://slack.com/api/oauth.access', json={
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
    })
    data = r.json()

    token = data['access_token']
    r = requests.post('https://slack.com/api/auth.test', json={
        'token': token,
    })
    data = r.json()
    tokens[data['user_id']] = token

    return jsonify({'ok': True})


@app.route('/command', methods=['POST'])
def command():
    channel = request.form['channel_id']
    user = request.form['user_id']
    user_name = request.form['user_name']
    spoiler = request.form['text']
    token = tokens[user]

    callback_id = uuid4()
    spoilers[callback_id] = spoiler

    requests.post('https://slack.com/api/chat.postMessage', json={
        'token': token,
        'channel': channel,
        'as_user': True,
        'attachments': [
            {
                'text': '{} wrote a spoiler!'.format(user_name),
                'fallback': '{} wrote a spoiler!'.format(user_name),
                'callback_id': callback_id,
                'actions': [
                    {
                        'name': 'show_spoiler',
                        'text': 'Show spoiler',
                        'type': 'button',
                        'confirm': {
                            'title': 'Are you sure?',
                            'text': 'You will be spoiled!',
                            'ok_text': 'Bring it on',
                            'dismiss_text': 'Nope',
                        },
                    }
                ],
            }
        ],
        'response_type': 'ephemeral',
    })

    return jsonify({'ok': True})


@app.route('/interact', methods=['POST'])
def interact():
    data = json.loads(request.form['payload'])
    spoiler = spoilers[data['callback_id']]
    return jsonify({'text': spoiler})


if __name__ == '__main__':
    app.run(debug=True)
