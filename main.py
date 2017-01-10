import sys
from lib.core import query_cmr, download, convert_to_geotiff, push_to_s3, get_s3_folder, make_index


def main(date):
    tiles = query_cmr(date, date)
    for tile in tiles:
        file = download(tile['url'])
        files = convert_to_geotiff(file)
        folder = get_s3_folder(file)
        index_fname = make_index(tile['thumb'], file, files)
        files.append(index_fname)
        for f in files:
            push_to_s3(f, 'modis-pds', folder)

if __name__ == '__main__':
    main(date=sys.argv[1])