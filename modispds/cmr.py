"""
Client library for using NASAs CMR API for searching and downloading from NASA data holdings
"""

import os
import requests
import sys
from urllib2 import HTTPError, urlopen
from json import load
from codecs import getreader
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
if sys.version_info < (3, 0):
    from HTMLParser import HTMLParser
else:
    from html.parser import HTMLParser

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

PROVIDER = os.getenv('PROVIDER', 'LPDAAC_ECS')
PRODUCT = os.getenv('PRODUCT', 'MCD43A4.006')
PAGE_SIZE = int(os.getenv('PAGE_SIZE', '1000'))

EARTHDATA_USER = os.getenv('EARTHDATA_USER')
EARTHDATA_PASS = os.getenv('EARTHDATA_PASS')


def query(start_date, end_date):
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
                entry_meta['url'] = str(url_entry['href'])
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
