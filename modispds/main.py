import sys
import time
import os
import datetime
import logging
import argparse
import subprocess
from dateutil.parser import parse
from modispds.earthdata import query, download_granule
from modispds.pds import push_to_s3, s3_list, make_index, make_scene_list, exists
import gippy
from modispds.version import __version__
from modispds.products import products

# quiet these loggers
logging.getLogger('boto3').setLevel(logging.CRITICAL)
logging.getLogger('botocore').setLevel(logging.CRITICAL)
logging.getLogger('nose').setLevel(logging.CRITICAL)
logging.getLogger('requests').setLevel(logging.CRITICAL)

fmt = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
logging.basicConfig(level=logging.INFO, format=fmt, datefmt='%m-%d-%Y %H:%M')
logger = logging.getLogger(__name__)

# default product
_PRODUCT = 'MCD43A4.006'

# environment variables
bucket = os.getenv('BUCKET', 'modis-pds')


def ingest(start_date, end_date, product=_PRODUCT, outdir='', overwrite=False):
    """ Ingest all granules between two dates """
    d1 = parse(start_date)
    d2 = parse(end_date)
    dates = [d1 + datetime.timedelta(n) for n in range((d2 - d1).days)]
    for day in [d.date() for d in dates]:
        start = datetime.datetime.now()
        index_fname = str(day) + '_scenes.txt'
        if exists(os.path.join('s3://%s' % bucket, os.path.join(product, index_fname))) and not overwrite:
            logger.info("Scenes for %s already processed" % day)
            continue
        logger.info('Processing date %s' % day)
        granules = query(day, day, product=product)

        metadata = []
        try:
            for gran in granules:
                metadata.append(ingest_granule(gran, outdir=outdir))
        except RuntimeError as e:
            logger.error('Error processing %s: %s' % (day, str(e)))
            # skip this entire date for now
            continue
        # upload index file
        if len(granules) > 0:
            fname = make_scene_list(metadata, fout=index_fname)
            push_to_s3(fname, bucket, prefix=product)
        logger.info('Completed processing %s: %s' % (day, datetime.datetime.now() - start))


def ingest_granule(gran, outdir='', prefix=''):
    """ Fetch granule, process, and push to s3 """
    bname = os.path.basename(gran['links'][0]['href'])
    gid = os.path.splitext(bname)[0]
    start_time = time.time()
    logger.debug('Processing granule %s' % gid)

    # create geotiffs
    logger.debug('Downloading granule %s' % gid)
    fnames = download_granule(gran, outdir=outdir)

    logger.debug('Converting granule to GeoTIFFs')
    files = convert_to_geotiff(fnames[0])

    # create index.html
    files.extend(fnames[2:])
    index_fname = make_index(fnames[1], bname, files)
    files.append(index_fname)
    files.append(fnames[1])

    # upload files to s3
    path = get_s3_path(bname, prefix=prefix)
    logger.debug('Uploading files to s3://%s/%s' % (bucket, path))
    s3fnames = []
    for f in files:
        s3fnames.append(push_to_s3(f, bucket, path))
        # cleanup
        os.remove(f)

    # cleanup original download
    os.remove(fnames[0])

    logger.info('Completed processing granule %s in : %ss' % (gid, time.time() - start_time))
    return {
        'gid': gid,
        'date': get_date(gid),
        'download_url': os.path.join('https://%s.s3.amazonaws.com' % bucket, path, 'index.html')
    }


def convert_to_geotiff(hdf, outdir=''):
    bname = os.path.basename(hdf)
    parts = bname.split('.')
    product = parts[0] + '.' + parts[3]
    bandnames = products[product]['bandnames']
    overviews = products[product]['overviews']
    file_names = []
    img = gippy.GeoImage(hdf, True)
    opts = {'COMPRESS': 'DEFLATE', 'PREDICTOR': '2', 'TILED': 'YES', 'BLOCKXSIZE': '512', 'BLOCKYSIZE': '512'}
    # save each band as a TIF
    for i, band in enumerate(img):
        fname = os.path.join(outdir, bname.replace('.hdf', '') + '_' + bandnames[i] + '.TIF')
        logger.debug('Writing %s' % fname)
        imgout = img.select([i+1]).save(fname, options=opts)
        imgout = None
        file_names.append(fname)
        # add overview as separate file
        if overviews[i]:
            cmd = 'gdaladdo -ro -r average --config COMPRESS_OVERVIEW DEFLATE %s 2 4 8' % fname
            logger.debug('Creating overviews: %s' % cmd)
            out = subprocess.check_output(cmd.split(' '))
            logger.debug(out)
            file_names.append(fname + '.ovr')

    return file_names


def granule_exists(granule, prefix=''):
    """ Check if the granule exists already on AWS """
    s3path = os.path.join('s3://%s' % bucket, get_s3_path(granule, prefix=prefix))
    urls = s3_list(s3path)
    return True if len(urls) == 18 else False


def get_s3_path(gid, prefix=''):
    """ Generate complete path in an S3 bucket (not including bucket name) """
    parts = gid.split('.')
    prod = '%s.%s' % (parts[0], parts[3])
    tile = parts[2].replace('h', '').replace('v', os.path.sep)
    date = parts[1].replace('A', '')
    path = os.path.join(prod, tile, date)
    if prefix != '':
        path = os.path.join(prefix, path)
    return path


def get_date(gid):
    """ Get date from granule ID """
    d = gid.split('.')[1].replace('A', '')
    return datetime.datetime.strptime(d, '%Y%j')


def parse_args(args):
    """ Parse arguments for the NDWI algorithm """
    desc = 'MODIS Public Dataset Utility (v%s)' % __version__
    dhf = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(description=desc, formatter_class=dhf)
    parser.add_argument('--version', help='Print version and exit', action='version', version=__version__)

    parser.add_argument('start_date', help='First date')
    parser.add_argument('end_date', help='End date')
    parser.add_argument('-p', '--product', default=_PRODUCT)
    parser.add_argument('--overwrite', default=False, action='store_true')
    parser.add_argument('--loglevel', default=2, type=int)

    return parser.parse_args(args)


def cli():
    args = parse_args(sys.argv[1:])
    ingest(args.start_date, args.end_date, product=args.product, overwrite=args.overwrite)


if __name__ == "__main__":
    cli()
