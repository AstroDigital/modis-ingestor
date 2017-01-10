import sys
from core import query_cmr, download, convert_to_geotiff, push_to_s3


def main:
    date = sys.argv[1]
    tiles = query_cmr(date, date)
    for tile in tiles:
        file = download(tile['url'])
        files = convert_to_geotiff(file)
        for f in files:
            push_to_s3(f)

if __name__ == '__main__':
    main()
