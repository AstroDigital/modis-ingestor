import sys
import time
import os
from modispds.cmr import query_cmr, download
from modispds.pds import push_to_s3, make_index
from json import dump
import gippy


def get_product_name(filename):
    return filename.split('.')[0] + '.' + filename.split('.')[3]


def get_tile_id(filename):
    return filename.split('.')[2].replace('h', '').replace('v', '/')


def get_date(filename):
    return filename.split('.')[1].replace('A', '')


def get_s3_folder(filename):
    return '%s/%s/%s' % (get_product_name(filename), get_tile_id(filename),
                         get_date(filename))


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


def main(date):
    products = query_cmr(date, date)
    for product in products:
        product_name = str(os.path.basename(product['url'])).replace('.hdf', '')
        print('Processing tile %s' % product_name)
        start_time = time.time()
        file = download(product['url'])
        files = convert_to_geotiff(str(file))
        folder = get_s3_folder(file)
        index_fname = make_index(product['thumb'], file, files)
        files.append(index_fname)
        for f in files:
            push_to_s3(f, 'modis-pds', folder)

        elapsed_time = time.time() - start_time
        print('Elapsed time for %s: %ss' % (product_name, str(elapsed_time)))


def cli():
    main(date=sys.argv[1])
