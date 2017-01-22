from __future__ import print_function

import datetime
import json
import sys
import traceback
import urllib2
import urlparse
from urllib import urlencode
from urllib2 import urlopen

import boto3
from boto3.s3.transfer import TransferConfig

import pytz
import requests

bucket_prefix = 'proj_max_'
_now = datetime.datetime.utcnow()
# make "now" timezone aware to compare to the bucket creation time
_now = pytz.utc.localize(_now)
now = _now.strftime("%Y%m%d_%H%M%S.%f")

bucket_name = bucket_prefix + now
file_size_limit = 1024 * 1024 * 1024  # 1 GB
bucket_max_age = 3600  # number of seconds
oldest_bkt = _now - datetime.timedelta(seconds=bucket_max_age)

chunk_size = 64 * 1024


def parse_url_and_validate(url):
    parse_result = urlparse.urlparse(url)
    if not parse_result.scheme:
        raise ValueError('Invalid URL: ' + url)
    # only support stuff from dropbox
    if 'dropbox.com' not in parse_result.netloc:
        raise ValueError('Curently we only support downloads from Dropbox')

    # update the query from dl=0 to dl=1 to force download
    url_parts = list(parse_result)
    query = dict(urlparse.parse_qsl(url_parts[4]))
    query.update({'dl': 1})
    url_parts[4] = urlencode(query)
    new_url = urlparse.urlunparse(url_parts)

    # if the shared link is for a single file, the link contains the file name
    # if the link is on a directory, the link does not contain the file name
    # when I download from the link using chrome, it knows to create a zip file
    # in the format of <directory name>.zip, but I don't know how it figures that out
    parts = parse_result.path.split('/')
    filename = urllib2.unquote(parts[-1])

    # dropbox ?dl=1 means to force download
    return filename, new_url


# def download_content(url, filename):
#     print('Downloading from ' + url)
#
#     response = urlopen(url)
#     with open(filename, 'wb') as f:
#         shutil.copyfileobj(response, f, chunk_size)
#
#
# def upload_to_s3(bucket_name, local_file, s3_file):
#     s3 = boto3.resource('s3')
#     print('Creating a s3 bucket ' + bucket_name)
#     s3.create_bucket(Bucket=bucket_name)
#     print('Uploading file name = ' + s3_file)
#     s3.Object(bucket_name, s3_file).put(Body=open(local_file, 'rb'))


def download_from_url_and_upload_to_s3(url, bucket_name, s3_file):
    s3 = boto3.resource('s3')
    bucket = s3.create_bucket(Bucket=bucket_name)
    print('Created a s3 bucket ' + bucket_name)

    file = bucket.Object(s3_file)
    try:
        file.upload_fileobj(urlopen(url), Config=TransferConfig())
        print('Created file ' + s3_file + ' in the bucket')
    except:
        raise

    client = boto3.client('s3')
    public_url = client.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': bucket_name,
            'Key': s3_file,
        },
        ExpiresIn=300
    )
    print("public URL = " + public_url)
    return public_url


def clean_older_files():
    s3 = boto3.resource('s3')
    old_bkts = filter(
        lambda bkt: bkt.name.startswith(bucket_prefix) and bkt.creation_date < oldest_bkt,
        s3.buckets.all())

    client = boto3.client('s3')
    for bkt in old_bkts:
        print('Deleting old bucket ' + bkt.name)
        for file in bkt.objects.all():
            client.delete_object(Bucket=bkt.name, Key=file.key)
        bkt.delete()


def respond(err, res=None, msg_type='ephemeral'):
    if msg_type != 'ephemeral' and msg_type != 'in_channel':
        msg_type = 'ephemeral'
    if err:
        msg = 'Aww snap, looks like something went wrong... '
        if err.message:
            msg += err.message
        else:
            msg += str(err)
    else:
        msg = json.dumps(res)

    return {
        'statusCode': 400 if err else 200,
        'response_type': 'ephemeral' if err else msg_type,
        'text': msg,
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def lambda_handler(event, context):
    print('received event: ' + json.dumps(event, indent=2))

    expected_token = '{{ slack.key }}'
    token = event['token']
    link = event['text']
    user = event['user_name']
    response_url = event['response_url']

    if token != expected_token:
        print("Request token (%s) does not match expected", token)
        r = respond(Exception('Invalid request token'))
        # TODO - fix the http return code, it's always 200
        return r
    else:
        r = respond(None,
                    res='We received your request. However, depending on the size of '
                        'your file, this could take up to a minute.',
                    msg_type='ephemeral')
        requests.post(response_url, json=r)

    try:
        clean_older_files()
        (file_name, download_url) = parse_url_and_validate(link)

        public_url = download_from_url_and_upload_to_s3(download_url, bucket_name, file_name)
    except:
        print(traceback.format_exc())
        r = respond(sys.exc_value)
        requests.post(response_url, json=r)
        # return r
    else:
        r = respond(None,
                    res='hi %s, the content of your Dropbox shared link can be '
                        'downloaded from %s. But hurry up, it expires in 5 minutes.'
                        % (user, public_url),
                    msg_type='in_channel'
                    )
        requests.post(response_url, json=r)
        # return r


if __name__ == '__main__':
    # link = 'https://www.dropbox.com/s/k9vrcskvxarp4wr/Docker_for_Java_Developers_NGINX.pdf?dl=1'
    # link = 'https://www.dropbox.com/sh/gb4ys9jbhs9qdxj/AAD2VIvc4Qy20oxNbTAOHuBXa?dl=1'

    event = {
        # "text": "https://www.dropbox.com/s/kwp2h88va2ndw41/RPM%20chapter1.doc?dl=0",
        "text": "https://dropbox.com/stuff",
        "token": "{{ slack.key }}",
        "user_name": "joan",
        "response_url": "https://hooks.slack.com/commands/T0CPLA68H/130976742101/Ly5ov0fvf60kBGL4aI9HlCeB"
    }

    context = ''
    response = lambda_handler(event, context)
    print(response)
