import os
from urllib2 import HTTPError, urlopen
from json import load, loads
from codecs import getreader

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
