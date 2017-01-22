import json

import requests

# with open('input.json') as f:
#     data = json.loads(f.read())

url = 'https://0rqthtkkkb.execute-api.us-east-1.amazonaws.com/prod/max'

data = {
    'url': 'https://stuff.com',
    'email': 'abc@yahoo.com'
}

# data = 'x'
r = requests.post(url, json=data)
print json.loads(r.text)
