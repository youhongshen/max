import json

import requests

# with open('input.json') as f:
#     data = json.loads(f.read())

url = 'https://0rqthtkkkb.execute-api.us-east-1.amazonaws.com/prod/max'

data = {
    "headers": {
        "Content-Type": "application/json"
    },
    # "text": "https://www.dropbox.com/s/kwp2h88va2ndw41/RPM%20chapter1.doc?dl=0",
    "text": "https://dropbox.com/stuff",
    "token": "some_token",
    "user_name": "joan",
    "response_url": "https://hooks.slack.com/commands/T0CPLA68H/130976742101/Ly5ov0fvf60kBGL4aI9HlCeB"
}

# data = 'x'
r = requests.post(url, json=data)
print('status code = %d' % r.status_code)
print('response = %s' % r.text)
