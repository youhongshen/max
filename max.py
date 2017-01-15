from __future__ import print_function

import datetime
import os
import shutil
import urllib2
from urllib2 import urlopen

import boto3

link = 'https://www.dropbox.com/s/k9vrcskvxarp4wr/Docker_for_Java_Developers_NGINX.pdf?dl=1'
link = 'https://www.dropbox.com/s/kwp2h88va2ndw41/RPM%20chapter1.doc?dl=0'


def parse_name(url):
    parts = url.split('/')
    last = parts[-1]  # filename?dl=0
    (tmp_name, _) = last.split('?')
    filename = urllib2.unquote(tmp_name)

    # dropbox ?dl=1 means to force download
    if 'dropbox.com' in url:
        url = url.replace('?dl=0', '?dl=1')
    return filename, url


def download_content(url, filename):
    print('Downloading from ' + url)

    response = urlopen(url)
    chunk_size = 16 * 1024
    with open(filename, 'wb') as f:
        shutil.copyfileobj(response, f, chunk_size)


def upload_to_s3(bucket_name, local_file, s3_file):
    s3 = boto3.resource('s3')
    print('Creating a s3 bucket ' + bucket_name)
    s3.create_bucket(Bucket=bucket_name)
    print('Uploading file name = ' + s3_file)
    s3.Object(bucket_name, s3_file).put(Body=open(local_file, 'rb'))


if __name__ == '__main__':
    try:
        bucket_prefix = 'proj_max_'
        now = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S.%f")
        bucket_name = bucket_prefix + now

        (file_name, download_url) = parse_name(link)
        # /tmp/<timestamp>_<orig file name>
        local_file = os.path.join(os.path.sep, 'tmp', now + '_' + file_name)
        download_content(download_url, local_file)

        upload_to_s3(bucket_name, local_file, file_name)
    #     assume if there's an exception, the stderr would be logged by lambda
    finally:
        os.remove(local_file)
