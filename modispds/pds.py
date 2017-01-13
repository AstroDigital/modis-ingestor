"""
Utilities for putting data up on AWS's Public Datasets (PDS)
"""
import os
import boto3
from jinja2 import Environment, FileSystemLoader, select_autoescape

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

path = os.path.dirname(__file__)

# for jinja2 templating
jinja_env = Environment(
    loader=FileSystemLoader(['templates', os.path.join(path, 'templates')]),
    autoescape=select_autoescape(['html', 'xml'])
)
template = jinja_env.get_template('index.html')


def push_to_s3(filename, bucket, folder):
    """ Copy file to S3 """
    print(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    key = '%s/%s' % (folder, os.path.basename(filename))
    print(bucket, key)
    with open(filename, 'rb') as f:
        print('Uploading %s to: %s' % (key, bucket))
        if 'html' in filename:
            content_type = 'text/html'
        elif 'json' in filename:
            content_type = 'application/json'
        else:
            content_type = 'binary/octet-stream'
        resp = s3.put_object(Bucket=bucket, Key=key, Body=f, ACL='public-read', ContentType=content_type)
    return 's3://%s/%s' % (bucket, key)


def make_index(thumb, product, files):
    html = template.render(thumb=thumb, product=product, files=files)
    index_fname = 'index.html'
    with open(index_fname, 'w') as outfile:
        print('Writing %s' % index_fname)
        outfile.write(html)

    return index_fname
