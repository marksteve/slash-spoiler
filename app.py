from os import environ
from urllib import urlencode
from uuid import uuid4

import porc
import requests
from flask import Flask, json, jsonify, redirect, request

application = app = Flask(__name__)

client_id = environ['SLACK_CLIENT_ID']
client_secret = environ['SLACK_CLIENT_SECRET']
# verification_token = environ['SLACK_VERIFICATION_TOKEN']

db = porc.Client(environ['ORCHESTRATE_API_KEY'])


@app.route('/auth')
def auth():
    return redirect('https://slack.com/oauth/authorize?{}'.format(urlencode({
        'client_id': client_id,
        'scope': 'commands chat:write:user',
    })))


@app.route('/oauth')
def oauth():
    code = request.args['code']
    r = requests.post('https://slack.com/api/oauth.access', data={
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
    })
    data = r.json()

    token = data['access_token']
    r = requests.post('https://slack.com/api/auth.test', data={
        'token': token,
    })
    data = r.json()
    db.put('tokens', data['user_id'], {'value': token})

    return "You can now spoil with /spoil!"


@app.route('/command', methods=['POST'])
def command():
    channel = request.form['channel_id']
    user = request.form['user_id']
    spoiler = request.form['text']

    token = db.get('tokens', user)['value']

    callback_id = uuid4()
    db.put('spoilers', callback_id, {'value': spoiler})

    requests.post('https://slack.com/api/chat.postMessage', data={
        'token': token,
        'channel': channel,
        'as_user': True,
        'attachments': json.dumps([
            {
                'text': 'Spoiler alert!',
                'fallback': 'Spoiler alert!',
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
        ]),
    })

    return ""


@app.route('/interact', methods=['POST'])
def interact():
    data = json.loads(request.form['payload'])
    spoiler = db.get('spoilers', data['callback_id'])['value']
    return jsonify({
        'text': spoiler,
        'replace_original': False,
        'response_type': 'ephemeral',
        'icon_emoji': ':zipper_mouth_face:',
    })


if __name__ == '__main__':
    app.run(debug=True)
