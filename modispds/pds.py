"""
Utilities for putting data up on AWS's Public Datasets (PDS)
"""
import os
import logging
import boto3

# environment variables
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# for jinja2 templating
from jinja2 import Environment, FileSystemLoader, select_autoescape
jinja_env = Environment(
    loader=FileSystemLoader(['templates', os.path.join(os.path.dirname(__file__), 'templates')]),
    autoescape=select_autoescape(['html', 'xml'])
)
template = jinja_env.get_template('index.html')
logger = logging.getLogger(__name__)


def splitall(path):
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path:  # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts


def push_to_s3(filename, bucket, prefix=''):
    """ Copy file to S3 """
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

    key = os.path.join(prefix, os.path.basename(filename))

    ext = os.path.splitext(filename)[1]
    with open(filename, 'rb') as f:
        logger.info('Uploading %s to: %s' % (key, bucket))
        if ext == '.html':
            content_type = 'text/html'
        elif ext == '.json':
            content_type = 'application/json'
        else:
            content_type = 'binary/octet-stream'
        resp = s3.put_object(Bucket=bucket, Key=key, Body=f, ACL='public-read', ContentType=content_type)
    return os.path.join('s3://%s' % bucket, key)


def del_from_s3(url):
    """ Remove file from S3 """
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    logger.info('Deleting %s' % url)
    parts = splitall(url)
    bucket = parts[1]
    key = os.path.sep.join(parts[2:])
    res = s3.delete_object(Bucket=bucket, Key=key)


def make_index(thumb, product, files):
    html = template.render(thumb=thumb, product=product, files=files)
    index_fname = 'index.html'
    with open(index_fname, 'w') as outfile:
        logger.info('Writing %s' % index_fname)
        outfile.write(html)

    return index_fname
