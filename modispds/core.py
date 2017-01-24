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


def get_product_name(filename):
    return filename.split('.')[0] + '.' + filename.split('.')[3]


def get_tile_id(filename):
    return filename.split('.')[2].replace('h', '').replace('v', '/')


def get_date(filename):
    return filename.split('.')[1].replace('A', '')


def get_s3_folder(filename):
    return '%s/%s/%s' % (get_product_name(filename), get_tile_id(filename),
                         get_date(filename))


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


def main(date1, date2, outdir=''):
    granules = query(date1, date2)

    for gran in granules[0:1]:
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
        folder = get_s3_folder(bname)
        files.extend(fnames[2:])
        index_fname = make_index(fnames[1], bname, files)
        files.append(index_fname)

        # push to s3
        for f in files:
            push_to_s3(f, 'modis-pds', folder)

        logger.info('Completed processing granule %s in : %ss' % (bname, time.time() - start_time))


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
    main(args.start_date, args.end_date)


if __name__ == "__main__":
    cli()
