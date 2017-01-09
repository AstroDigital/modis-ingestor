import os
import sys
from urllib2 import HTTPError, urlopen
from json import load, loads
from codecs import getreader
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
if sys.version_info < (3, 0):
    from HTMLParser import HTMLParser
else:
    from html.parser import HTMLParser


PROVIDER = os.getenv('PROVIDER', 'LPDAAC_ECS')
PRODUCT = os.getenv('PRODUCT', 'MCD43A4.006')
PAGE_SIZE = int(os.getenv('PAGE_SIZE', '2'))


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
            if url_entry['type'] == 'application/x-hdfeos':
                entry_meta['url'] = url_entry['href']
                tile_meta.append(entry_meta)
                break

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


def download(url, path='./'):
    """ Get URL (without auth) and save with some name """
    fout = os.path.join(path, os.path.basename(url))
    auth = (os.environ.get('EARTHDATA_USER'), os.environ.get('EARTHDATA_PASS'))
    r = requests.get(url, auth=auth, allow_redirects=False)
    if r.status_code == 302:
        link = LinkFinder()
        link.feed(r.text)
        url = link.download_link
    else:
        raise Exception("Earthdata Authentication Error")

    # download as stream
    session = set_retries(2)
    stream = session.get(url, auth=auth, stream=True)
    chunk_size = 1024
    try:
        with open(fout, 'wb') as f:
            for chunk in stream.iter_content(chunk_size):
                f.write(chunk)
    except:
        raise Exception("Problem downloading %s" % url)

    return fout
