"""
Client library for using NASAs CMR API for searching and downloading from NASA data holdings
"""

import os
import requests
import datetime
from dateutil.parser import parse as dateparser
from json import dump
import logging
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from html.parser import HTMLParser
from dotenv import load_dotenv, find_dotenv
from cmr import GranuleQuery
from .products import products

# get environment variables
load_dotenv(find_dotenv())
EARTHDATA_USER = os.getenv('EARTHDATA_USER')
EARTHDATA_PASS = os.getenv('EARTHDATA_PASS')

# logging
logger = logging.getLogger(__name__)


def query(start_date, end_date, product='MCD43A4.006', provider='LPDAAC_ECS'):
    """ Search CMR database for spectral MODIS tiles matching a temporal range,
    defined by a start date and end date. Returns metadata containing the URL of
    each image.
    """
    q = GranuleQuery()
    prod, ver = product.split('.')
    q.short_name(prod).version(ver)
    q.temporal('%sT00:00:00Z' % str(start_date), '%sT23:59:00Z' % str(end_date))
    _granules = q.get_all()

    # filter dates
    day_offset = products[product]['day_offset']
    granules = []
    for gran in _granules:
        # CMR uses day 1 of window - correct this to be middle of window
        date = (dateparser(gran['time_start'].split('T')[0]) + datetime.timedelta(days=day_offset)).date()
        if (start_date <= date <= end_date):
            granules.append(gran)
    logger.info("%s granules found within %s - %s" % (len(granules), start_date, end_date))
    return granules


def download_granule(meta, outdir=''):
    """ Download granule files from metadata instance """
    # get basename
    url = str(meta['links'][0]['href'])
    bname = os.path.splitext(os.path.basename(url))[0]

    # save metadata
    fn_meta = os.path.join(outdir, bname + '_meta.json')
    with open(fn_meta, 'w') as f:
        logger.debug('Writing metadata to %s' % fn_meta)
        dump(meta, f, sort_keys=True, indent=4, ensure_ascii=False)

    # download hdf
    fn_hdf = download_file(url, outdir=outdir)

    links = {m['type']: m['href'] for m in meta['links'][1:] if 'type' in m}
    # download xml metadata
    fn_metaxml = download_file(links['text/xml'], outdir=outdir)
    # download browse image
    fn_browse = download_file(links['image/jpeg'], noauth=True, outdir=outdir)

    return [fn_hdf, fn_browse, fn_meta, fn_metaxml]


def download_file(url, noauth=False, outdir=''):
    """ Get URL and save with some name """
    fout = os.path.join(outdir, os.path.basename(url))
    auth = () if noauth else (EARTHDATA_USER, EARTHDATA_PASS)
    # download as stream
    session = get_session(retries=5)
    if noauth:
        stream = session.get(url, stream=True)
    else:
        stream = get_stream(session, url, auth, [])
    chunk_size = 1024
    try:
        with open(fout, 'wb') as f:
            logger.debug('Saving %s' % fout)
            for chunk in stream.iter_content(chunk_size):
                f.write(chunk)
    except:
        raise RuntimeError("Problem fetching %s" % stream)

    return fout


def get_session(retries=5):
    s = requests.Session()
    r = Retry(total=retries, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    s.mount('http://', HTTPAdapter(max_retries=r))
    s.mount('https://', HTTPAdapter(max_retries=r))
    return s


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
        raise RuntimeError("Earthdata Authentication Error")


class LinkFinder(HTMLParser):
    def __init__(self):
        self.reset()
        self.download_link = None

    def handle_starttag(self, tag, attrs):
        if attrs and attrs[0][0] == 'href':
            self.download_link = attrs[0][1]
