import sys
from lib.core import query_cmr, download, convert_to_geotiff, push_to_s3, get_s3_folder, make_index


def main(date):
    tiles = query_cmr(date, date)
    for tile in tiles:
        file = 'MCD43A4.A2011358.h03v11.006.2016139165208.hdf'
        # file = download(tile['url'])
        files = convert_to_geotiff(file)
        folder = get_s3_folder(file)

        # create the index.html and add to the files array for uploading
        index_fname = 'index.html'
        with open(index_fname, 'w') as outfile:
            html = make_index(tile['thumb'], file, files)
            outfile.write(index)
            files.append(index_fname)
        for f in files:
            push_to_s3(f, 'modis-pds', folder)

if __name__ == '__main__':
    main(date=sys.argv[1])
