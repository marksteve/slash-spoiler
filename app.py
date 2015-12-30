from os import environ

import requests
from flask import abort, Flask, request

application = app = Flask(__name__)

slack = requests.Session()
slack.params.update({
    'token': environ['SLACK_API_TOKEN'],
})
slash_token = environ['SLACK_SLASH_COMMAND_TOKEN']


def get_slack_users():
    return {
        user['id']: user for user in
        slack.get('https://slack.com/api/users.list').json()['members']
    }


@app.route('/', methods=['POST'])
def handler():
    if request.form['token'] != slash_token:
        abort(403)
    return "SPOILERS"


if __name__ == '__main__':
    app.run(debug=True)
