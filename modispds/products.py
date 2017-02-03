# MODIS product configuration

products = {
    'MCD43A4.006': {
        'day_offset': 8,
        'bandnames':
            ['B%sqa' % str(i).zfill(2) for i in range(1, 8)] +
            ['B%s' % str(i).zfill(2) for i in range(1, 8)],
        'overviews': ([False] * 7) + ([True] * 7)
    }
}
