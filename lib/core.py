import os
import sys
from urllib2 import HTTPError, urlopen
from json import load, loads, dump
from codecs import getreader
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import gippy
import boto3
from jinja2 import Environment, FileSystemLoader, select_autoescape

if sys.version_info < (3, 0):
    from HTMLParser import HTMLParser
else:
    from html.parser import HTMLParser


PROVIDER = os.getenv('PROVIDER', 'LPDAAC_ECS')
PRODUCT = os.getenv('PRODUCT', 'MCD43A4.006')
PAGE_SIZE = int(os.getenv('PAGE_SIZE', '1000'))
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
EARTHDATA_USER = os.getenv('EARTHDATA_USER')
EARTHDATA_PASS = os.getenv('EARTHDATA_PASS')

# for jinja2 templating
jinja_env = Environment(
    loader=FileSystemLoader(['templates', 'lib/templates']),
    autoescape=select_autoescape(['html', 'xml'])
)
template = jinja_env.get_template('index.html')


def query_cmr(start_date, end_date):
    """ Search CMR database for spectral MODIS tiles matching a temporal range,
    defined by a start date and end date. Returns metadata containing the URL of
    each image.
    """

    prod, ver = PRODUCT.split('.')
    query = 'https://cmr.earthdata.nasa.gov/search/granules.json?' + \
            'provider={0}&short_name={1}&version={2}'.format(
             PROVIDER, prod, ver) + \
            '&online_only=true&page_size={0}&sort_key=start_date'.format(
             PAGE_SIZE) + \
            '&temporal={0}T00:00:00Z,{1}T23:59:00Z'.format(
             start_date, end_date)
    print('searching ' + query)
    try:
        response = urlopen(query)
    except HTTPError as error:
        raise ValueError('The CMR server returned the following error:',
                         error.read())

    json_data = load(getreader("utf-8")(response))
    tile_meta = []
    for entry in json_data['feed']['entry']:
        date = entry['time_start'].split('T')[0]
        entry_meta = {'date': date}
        for url_entry in entry['links']:
            if url_entry.get('type') == 'application/x-hdfeos' and 'opendap' not in url_entry.get('href'):
                entry_meta['url'] = url_entry['href']
            if url_entry.get('type') == 'image/jpeg':
                entry_meta['thumb'] = url_entry['href']

        tile_meta.append(entry_meta)
    response.close()

    return tile_meta


def set_retries(retries):
    s = requests.Session()
    r = Retry(total=retries, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    s.mount('http://', HTTPAdapter(max_retries=r))
    s.mount('https://', HTTPAdapter(max_retries=r))
    return s


class LinkFinder(HTMLParser):
    def __init__(self):
        self.reset()
        self.download_link = None

    def handle_starttag(self, tag, attrs):
        if attrs and attrs[0][0] == 'href':
            self.download_link = attrs[0][1]


def get_stream(session, url, auth, previous_tries):
    """ Traverse redirects to get the final url """
    stream = session.get(url, auth=auth, allow_redirects=False, stream=True)
    # if we get back to the same url, it's time to download
    if url in previous_tries:
        return stream
    if stream.status_code == 302:
        previous_tries.append(url)
        link = LinkFinder()
        link.feed(stream.text)
        return get_stream(session, link.download_link, auth, previous_tries)
    else:
        raise Exception("Earthdata Authentication Error")


def download(url, path=''):
    """ Get URL and save with some name """
    fout = os.path.join(path, os.path.basename(url))
    auth = (EARTHDATA_USER, EARTHDATA_PASS)
    # download as stream
    session = set_retries(5)
    stream = get_stream(session, url, auth, [])
    chunk_size = 1024
    try:
        with open(fout, 'wb') as f:
            print('Writing %s' % fout)
            for chunk in stream.iter_content(chunk_size):
                f.write(chunk)
    except:
        raise Exception("Problem downloading %s" % stream)

    return fout


def convert_to_geotiff(hdf, path=''):
    file_names = []
    img = gippy.GeoImage(hdf, True)
    # write out metadata
    metadata_fname = 'metadata.json'
    with open(metadata_fname, 'w') as outfile:
        print('Writing metadata')
        dump(img.meta(), outfile, sort_keys=True, indent=4, ensure_ascii=False)
        file_names.append(metadata_fname)
    # save each band as a TIF
    for i, band in enumerate(img):
        fname = hdf.replace('.hdf', '') + '_B' + str(i+1).zfill(2) + '.TIF'
        print('Writing %s' % fname)
        imgout = img.select([i+1]).save(fname)
        file_names.append(fname)

    return file_names


def get_product_name(filename):
    return filename.split('.')[0] + '.' + filename.split('.')[3]


def get_tile_id(filename):
    return filename.split('.')[2].replace('h', '').replace('v', '/')


def get_date(filename):
    return filename.split('.')[1].replace('A', '')


def get_s3_folder(filename):
    return '%s/%s/%s' % (get_product_name(filename), get_tile_id(filename),
                         get_date(filename))


def push_to_s3(filename, bucket, folder):
    """ Copy file to S3 """
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    key = '%s/%s' % (folder, os.path.basename(filename))
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
