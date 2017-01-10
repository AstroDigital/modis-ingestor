import sys
from lib.core import query_cmr, download, convert_to_geotiff, push_to_s3, get_s3_folder


def main:
    date = sys.argv[1]
    tiles = query_cmr(date, date)
    for tile in tiles:
        file = download(tile['url'])
        files = convert_to_geotiff(file)
        folder = get_s3_folder(file)
        for f in files:
            push_to_s3(f, 'modis-pds', folder)

if __name__ == '__main__':
    main()
