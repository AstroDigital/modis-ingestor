import sys
from lib.core import query_cmr, download, convert_to_geotiff, push_to_s3, get_s3_folder, make_index
import time
import os


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

if __name__ == '__main__':
    main(date=sys.argv[1])
