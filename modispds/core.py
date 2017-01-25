import sys
import time
import os
import logging
import argparse
from modispds.cmr import query, download_granule
from modispds.pds import push_to_s3, make_index
import gippy
from modispds.version import __version__

logger = logging.getLogger(__name__)


def ingest(date1, date2, outdir=''):
    """ Ingest all granules between two dates """
    granules = query(date1, date2)

    for gran in granules:
        ingest_granule(gran, outdir=outdir)


def ingest_granule(gran, outdir='', bucket='modis-pds', prefix=''):
    """ Fetch granule, process, and push to s3 """
    url = gran['Granule']['OnlineAccessURLs']['OnlineAccessURL']['URL']
    bname = os.path.basename(url)
    start_time = time.time()
    logger.info('Processing tile %s' % bname)

    # create geotiffs
    logger.info("Downloading granule %s" % bname)
    fnames = download_granule(gran, outdir=outdir)

    logger.info("Converting to GeoTIFFs")
    files = convert_to_geotiff(fnames[0])

    # create index.html
    files.extend(fnames[2:])
    index_fname = make_index(fnames[1], bname, files)
    files.append(index_fname)

    # push to s3
    path = get_s3_path(bname, prefix=prefix)
    fnames = []
    for f in files:
        fnames.append(push_to_s3(f, 'modis-pds', path))

    logger.info('Completed processing granule %s in : %ss' % (bname, time.time() - start_time))
    return fnames


def convert_to_geotiff(hdf, outdir=''):
    bname = os.path.basename(hdf)
    file_names = []
    img = gippy.GeoImage(hdf, True)
    opts = {'COMPRESS': 'DEFLATE', 'PREDICTOR': '2', 'TILED': 'YES', 'BLOCKXSIZE': '512', 'BLOCKYSIZE': '512'}
    # save each band as a TIF
    for i, band in enumerate(img):
        fname = os.path.join(outdir, bname.replace('.hdf', '') + '_B' + str(i+1).zfill(2) + '.TIF')
        logger.info('Writing %s' % fname)
        imgout = img.select([i+1]).save(fname, overviews=True, options=opts)
        file_names.append(fname)

    return file_names


def get_s3_path(filename, prefix=''):
    """ Generate complete path in an S3 bucket (not including bucket name) """
    parts = filename.split('.')
    prod = '%s.%s' % (parts[0], parts[3])
    tile = parts[2].replace('h', '').replace('v', os.path.sep)
    date = parts[1].replace('A', '')
    path = os.path.join(prod, tile, date)
    if prefix != '':
        path = os.path.join(prefix, path)
    return path


def parse_args(args):
    """ Parse arguments for the NDWI algorithm """
    desc = 'MODIS Public Dataset Utility (v%s)' % __version__
    dhf = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(description=desc, formatter_class=dhf)
    parser.add_argument('--version', help='Print version and exit', action='version', version=__version__)

    parser.add_argument('start_date', help='First date')
    parser.add_argument('end_date', help='End date')

    return parser.parse_args(args)


def cli():
    args = parse_args(sys.argv[1:])
    ingest(args.start_date, args.end_date)


if __name__ == "__main__":
    cli()
