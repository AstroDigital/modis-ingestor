import sys
import time
import os
import logging
from modispds.cmr import query, download_granule
from modispds.pds import push_to_s3, make_index
from json import dump
import gippy

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
    # save each band as a TIF
    for i, band in enumerate(img):
        fname = os.path.join(outdir, bname.replace('.hdf', '') + '_B' + str(i+1).zfill(2) + '.TIF')
        logger.info('Writing %s' % fname)
        imgout = img.select([i+1]).save(fname)
        file_names.append(fname)

    return file_names


def main(date, outdir=''):
    granules = query(date, date)

    for gran in granules:
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

        index_fname = make_index(fnames[1], bname, files)
        files.append(index_fname)
        files.extend(fnames[1:])

        # push to s3
        for f in files:
            push_to_s3(f, 'modis-pds', folder)

        logger.info('Completed processing granule %s in : %ss' % (bname, time.time() - start_time))


def cli():
    main(date=sys.argv[1])
